"""Processor attribution, authorization, reporting, and historical backfill."""
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from payments.models import Payment
from payments.services.fulfillment import process_cash, serialize_payment
from payments.tests import CONFIG, Fixtures


@override_settings(**CONFIG)
class ProcessorAttributionTests(Fixtures, TestCase):
    def test_cash_members_and_walkins_ignore_spoofed_processor_and_keep_retry_identity(self):
        for customer in (self.member.member_id, 'GYMMSGUEST'):
            with self.subTest(customer=customer):
                self.staff.name = 'Original Name'
                self.staff.save()
                data = self.data(member_id=customer, processed_by=self.owner.pk,
                                 stored_processor_id=self.owner.pk, stored_processor_name='Spoofed')
                response = self.client.post('/payments/process/', data)
                self.assertEqual(response.status_code, 200)
                payment = Payment.objects.get(pk=response.json()['payment_id'])
                self.assertEqual(payment.processed_by_id, self.staff.pk)
                self.assertEqual(payment.stored_processor_id, self.staff.pk)
                self.assertEqual(payment.processor_display, 'Original Name (staff)')
                self.staff.name = 'Changed Name'
                self.staff.save()
                retried, _ = process_cash(self.staff, data)
                self.assertEqual(retried.pk, payment.pk)
                self.assertEqual(serialize_payment(retried)['processed_by'], 'Original Name (staff)')

    def test_qrph_snapshot_survives_rename_owner_reconciliation_and_duplicate_receipt(self):
        for customer in (self.member.member_id, 'GYMMSGUEST'):
            with self.subTest(customer=customer):
                self.staff.name = 'Checkout Name'
                self.staff.save()
                payload = self.data(member_id=customer, stored_processor_id=self.owner.pk,
                                    stored_processor_name='Spoofed', created_by=self.owner.pk)
                from payments.services import qrph
                attempt = qrph.create_attempt(self.staff, payload)
                self.assertEqual(attempt.stored_processor_id, self.staff.pk)
                self.staff.name = 'Name After Checkout'
                self.staff.save()
                self.assertEqual(qrph.create_attempt(self.staff, payload).stored_processor_name, 'Checkout Name')
                self.client.force_login(self.owner)
                self.assertEqual(self.client.get(f'/payments/qrph/attempts/{attempt.pk}/').status_code, 200)
                attempt = self.ready(attempt)
                self.settle(attempt)
                self.settle(attempt, 'evt_duplicate_' + customer)
                attempt.refresh_from_db()
                self.assertEqual(attempt.payment.processor_display, 'Checkout Name (staff)')
                self.assertEqual(attempt.payment.processed_by_id, self.staff.pk)
                self.assertEqual(Payment.objects.filter(pk=attempt.payment_id).count(), 1)

    def test_snapshots_and_payment_processor_cannot_be_reassigned(self):
        payment, _ = process_cash(self.staff, self.data())
        attempt = self.attempt(user=self.other, member_id='GYMMSGUEST')
        for instance in (payment, attempt):
            for field, value in [('stored_processor_id', self.owner.pk), ('stored_processor_username', 'fake'),
                                 ('stored_processor_name', 'fake')]:
                with self.subTest(model=type(instance).__name__, field=field):
                    instance.refresh_from_db()
                    setattr(instance, field, value)
                    with self.assertRaisesMessage(ValueError, 'immutable'):
                        instance.save(update_fields=[field])
            instance.refresh_from_db()
        payment.processed_by = self.owner
        with self.assertRaisesMessage(ValueError, 'immutable'):
            payment.save()
        attempt.created_by = self.owner
        with self.assertRaisesMessage(ValueError, 'immutable'):
            attempt.save(update_fields=['created_by'])

    def test_identity_survives_hard_delete_where_permitted(self):
        # No CashPaymentRequest or checkout protects this legacy account from deletion.
        payment = Payment.objects.create(processed_by=self.staff, amount=100)
        self.staff.delete()
        payment.refresh_from_db()
        self.assertIsNone(payment.processed_by)
        self.assertEqual(payment.processor_display, 'staff')
        payment.remarks = 'Still editable outside attribution'
        payment.save(update_fields=['remarks'])
        self.assertEqual(serialize_payment(payment)['processed_by'], 'staff')


class ProcessorReportingTests(Fixtures, TestCase):
    endpoints = ['/payments/transactions/', '/payments/transactions/ajax/', '/payments/transactions/stats/']

    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def payment(self, actor=None, **changes):
        return Payment.objects.create(processed_by=actor, amount=changes.pop('amount', Decimal('100.00')), **changes)

    def report(self, **params):
        return self.client.get(self.endpoints[1], {'period': 'all', **params}).json()

    def test_totals_group_renamed_owner_inactive_deleted_and_unknown_processors(self):
        self.payment(self.staff, payment_date=timezone.now() - timedelta(days=1))
        self.staff.name = 'Latest Name'
        self.staff.save()
        self.payment(self.staff)
        self.payment(self.staff, status='Failed')
        self.payment(self.staff, status='Refunded')
        self.payment(self.owner)
        self.payment(self.other)
        self.other.is_active = False
        self.other.save()
        deleted = get_user_model().objects.create_user(username='deleted', role='Staff')
        deleted_id = deleted.pk
        self.payment(deleted)
        deleted.delete()
        self.payment()
        result = self.report()
        self.assertEqual(result['stats'], {'total_revenue': 600, 'total_count': 6, 'average_amount': 100})
        rows = {row['processor']: row for row in result['processor_sales']}
        self.assertEqual(rows[str(self.staff.pk)]['total_revenue'], 200)
        self.assertEqual(rows[str(self.staff.pk)]['label'], 'Latest Name (staff)')
        self.assertEqual(rows[str(deleted_id)]['label'], 'deleted')
        self.assertEqual(rows['unknown']['label'], 'Unknown processor')
        self.assertIn(str(self.other.pk), rows)
        self.assertIn(str(self.owner.pk), rows)
        self.assertEqual(result['processor_sales'][0]['processor'], str(self.staff.pk))
        tied = [row['processor'] for row in result['processor_sales'][1:]]
        self.assertEqual(len(set(tied)), 4)
        # Identity snapshots also appear consistently on initial HTML and AJAX rows.
        self.assertContains(self.client.get(self.endpoints[0]), 'Latest Name (staff)')
        self.assertIn('staff', [row['processed_by'] for row in result['transactions']])

    def test_combined_filters_match_html_ajax_and_stats(self):
        now = timezone.now()
        self.payment(self.staff, stored_member_id='GYMMSGUEST', stored_member_name='Matching Guest', payment_method='QRPh')
        self.payment(self.other, stored_member_id='GYMMSGUEST', stored_member_name='Matching Guest', payment_method='QRPh')
        self.payment(self.staff, stored_member_id='GYMMSGUEST', stored_member_name='Different', payment_method='Cash')
        params = dict(processor=str(self.staff.pk), search='Matching', payment_method='Digital', member_type='walkin',
                      date_from=timezone.localdate(now).isoformat(), date_to=timezone.localdate(now).isoformat(), period='all')
        html = self.client.get(self.endpoints[0], params)
        ajax = self.client.get(self.endpoints[1], params).json()
        stats = self.client.get(self.endpoints[2], params).json()
        self.assertEqual(html.context['total_revenue'], 100)
        self.assertEqual(ajax['stats']['total_revenue'], 100)
        self.assertEqual(stats['total_revenue'], 100)
        self.assertEqual(html.context['processor_sales'], ajax['processor_sales'])
        self.assertEqual(stats['processor_sales'], ajax['processor_sales'])
        self.assertEqual(len(ajax['transactions']), 1)
        self.assertContains(html, f'value="{self.staff.pk}" selected')

    def test_summary_is_independent_of_pagination_and_period_does_not_filter_ledger(self):
        for _ in range(12):
            self.payment(self.staff)
        self.payment(self.staff, payment_date=timezone.now() - timedelta(days=10))
        result = self.report(page=2, per_page=10)
        self.assertEqual(len(result['transactions']), 3)
        self.assertEqual(result['processor_sales'][0]['total_count'], 13)
        recent = self.report(period='1d')
        self.assertEqual(recent['stats']['total_count'], 12)
        self.assertEqual(recent['pagination']['total_count'], 13)
        html = self.client.get(self.endpoints[0])
        self.assertEqual(html.context['total_count'], 12)
        self.assertContains(html, 'of 13 transactions')

    def test_date_bounds_override_period_and_use_manila_calendar_dates(self):
        manila = ZoneInfo('Asia/Manila')
        self.payment(self.staff, payment_date=datetime(2025, 1, 1, 0, 0, tzinfo=manila))
        self.payment(self.staff, payment_date=datetime(2025, 1, 1, 23, 59, 59, tzinfo=manila))
        self.payment(self.staff, payment_date=datetime(2025, 1, 2, 0, 0, tzinfo=manila))
        params = dict(date_from='2025-01-01', date_to='2025-01-01', period='1d')
        self.assertEqual(self.report(**params)['stats']['total_count'], 2)
        self.assertEqual(self.client.get(self.endpoints[2], params).json()['total_count'], 2)
        # A lone upper bound also overrides the preset.
        self.assertEqual(self.client.get(self.endpoints[2], {'date_to': '2025-01-01'}).json()['total_count'], 2)

    def test_unknown_and_nonexistent_processor_filters_and_empty_results(self):
        self.payment()
        self.payment(self.staff)
        unknown = self.report(processor='unknown')
        self.assertEqual(unknown['stats']['total_count'], 1)
        self.assertEqual(unknown['processor_sales'][0]['processor'], 'unknown')
        empty = self.report(processor='9223372036854775807')
        self.assertEqual(empty['processor_sales'], [])
        self.assertEqual(empty['pagination']['start_index'], 0)
        self.assertEqual(empty['stats']['average_amount'], 0)

    def test_permissions_and_validation_on_all_endpoints(self):
        self.payment(self.staff)
        for endpoint in self.endpoints:
            for invalid in ('abc', '-1', '0', '1.5', '9223372036854775808', '1' * 5000):
                with self.subTest(endpoint=endpoint, invalid=invalid[:20]):
                    self.assertEqual(self.client.get(endpoint, {'processor': invalid}).status_code, 400)
        self.client.force_login(self.staff)
        for endpoint in self.endpoints:
            self.assertEqual(self.client.get(endpoint, {'processor': self.staff.pk}).status_code, 403)
            self.assertEqual(self.client.get(endpoint, {'processor': ''}).status_code, 403)
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            if endpoint.endswith(('/ajax/', '/stats/')):
                self.assertNotIn('processor_sales', response.json())
                self.assertNotIn('processor_options', response.json())
            else:
                self.assertNotContains(response, 'id="processorFilter"')
                self.assertNotContains(response, 'id="processorSalesBody"')
                self.assertContains(response, 'Processed By')
        self.owner.is_active = False
        from payments.services.reporting import can_audit_processors
        self.assertFalse(can_audit_processors(self.owner))
        superuser = get_user_model().objects.create_user(username='super', role='Staff', is_superuser=True)
        self.client.force_login(superuser)
        self.assertIn('processor_sales', self.report())
        self.client.logout()
        for endpoint in self.endpoints:
            self.assertEqual(self.client.get(endpoint).status_code, 302)

    def test_decimal_sales_average_and_stable_revenue_ties(self):
        for amount in ('50.25', '150.75', '300.50'):
            self.payment(self.staff, amount=Decimal(amount))
        self.payment(self.owner, amount=Decimal('501.50'))
        self.payment(amount=Decimal('501.50'))
        rows = self.report()['processor_sales']
        self.assertEqual([row['processor'] for row in rows],
                         [str(self.staff.pk), str(self.owner.pk), 'unknown'])
        self.assertEqual(rows[0]['total_revenue'], 501.5)
        self.assertEqual(rows[0]['total_count'], 3)
        self.assertAlmostEqual(rows[0]['average_amount'], 501.5 / 3)
        html = self.client.get(self.endpoints[0], {'per_page': 100})
        self.assertContains(html, 'value="100" selected')

    def test_snapshot_html_is_escaped(self):
        self.staff.name = '<img src=x onerror=alert(1)>'
        self.staff.save()
        self.payment(self.staff)
        response = self.client.get(self.endpoints[0])
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')


class ProcessorMigrationTests(TransactionTestCase):
    initial = [('payments', '0001_initial')]
    incremental = [('payments', '0002_onlinepaymentattempt_stored_processor_id_and_more')]
    squashed = [('payments', '0001_squashed_0002_processor_audit')]

    def setUp(self):
        super().setUp()
        MigrationExecutor(connection).migrate([('payments', None)])
        self.addCleanup(self.restore_schema)

    def restore_schema(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def legacy_executor(self):
        from django.db.migrations.loader import MigrationLoader
        executor = MigrationExecutor(connection)
        executor.loader = MigrationLoader(connection, replace_migrations=False)
        return executor

    def historic_records(self, apps):
        user = apps.get_model('users', 'StaffUser').objects.create(username='historic', name='Historic Staff')
        ledger = apps.get_model('payments', 'Payment')
        known = ledger.objects.create(processed_by_id=user.pk)
        unknown = ledger.objects.create()
        import uuid
        attempt = apps.get_model('payments', 'OnlinePaymentAttempt').objects.create(
            created_by_id=user.pk, request_key=uuid.uuid4(), stored_member_id='GYMMSGUEST',
            customer_name='Guest', plan_label='Day', duration_days=1,
            amount=100, amount_centavos=10000, mode='live')
        return user, known, unknown, attempt

    def test_fresh_database_initializes_payments_once(self):
        executor = MigrationExecutor(connection)
        payment_plan = [(migration.name, backward) for migration, backward in executor.migration_plan(self.squashed)
                        if migration.app_label == 'payments']
        self.assertEqual(payment_plan, [('0001_squashed_0002_processor_audit', False)])
        executor.migrate(self.squashed)
        user = get_user_model().objects.create_user(username='fresh', name='Fresh Processor')
        payment = Payment.objects.create(processed_by=user, amount=100)
        self.assertEqual(payment.stored_processor_name, 'Fresh Processor')
        with connection.cursor() as cursor:
            fields = {field.name for field in connection.introspection.get_table_description(cursor, 'payments_onlinepaymentattempt')}
        self.assertTrue({'stored_processor_id', 'stored_processor_name', 'stored_processor_username'} <= fields)
        repeated = MigrationExecutor(connection)
        self.assertEqual(repeated.migration_plan(self.squashed), [])
        repeated.migrate(self.squashed)
        self.assertEqual(Payment.objects.get(pk=payment.pk).stored_processor_name, 'Fresh Processor')

    def test_incremental_backfill_preserves_known_and_unknown_attribution(self):
        executor = self.legacy_executor()
        executor.migrate(self.initial)
        apps = executor.loader.project_state(self.initial).apps
        user, known, unknown, attempt = self.historic_records(apps)
        # A partially upgraded database must run the original backfill, not recreate tables.
        executor = MigrationExecutor(connection)
        self.assertEqual([(migration.name, backward) for migration, backward in executor.migration_plan(self.incremental)],
                         [('0002_onlinepaymentattempt_stored_processor_id_and_more', False)])
        executor.migrate(self.incremental)
        restored = Payment.objects.get(pk=known.pk)
        self.assertEqual(restored.stored_processor_id, user.pk)
        self.assertEqual(restored.stored_processor_name, 'Historic Staff')
        self.assertEqual(restored.stored_processor_username, 'historic')
        self.assertIsNone(Payment.objects.get(pk=unknown.pk).stored_processor_id)
        from payments.models import OnlinePaymentAttempt
        checkout = OnlinePaymentAttempt.objects.get(pk=attempt.pk)
        self.assertEqual(checkout.stored_processor_id, user.pk)
        self.assertEqual(checkout.stored_processor_username, 'historic')
        # Later initialization must never overwrite snapshots with renamed account details.
        user.name = 'Later Name'
        user.save()
        executor = MigrationExecutor(connection)
        self.assertEqual(executor.migration_plan(self.squashed), [])
        executor.migrate(self.squashed)
        self.assertEqual(Payment.objects.get(pk=known.pk).stored_processor_name, 'Historic Staff')
        self.assertEqual(Payment.objects.count(), 2)

    def test_fully_upgraded_database_adopts_squash_without_replaying_schema(self):
        executor = self.legacy_executor()
        executor.migrate(self.incremental)
        payment = Payment.objects.create(amount=100)
        # Simulate an installation that applied both originals before the squash existed.
        from django.db.migrations.recorder import MigrationRecorder
        recorder = MigrationRecorder(connection)
        recorder.record_unapplied(*self.squashed[0])
        executor = MigrationExecutor(connection)
        self.assertEqual(executor.migration_plan(self.squashed), [])
        executor.migrate(self.squashed)
        self.assertIn(self.squashed[0], recorder.applied_migrations())
        self.assertEqual(Payment.objects.get(pk=payment.pk).amount, Decimal('100.00'))
