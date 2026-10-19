"""The incremental upgrade releases stuck staff workflows without changing receipts."""
import uuid

from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from payments.models import OnlinePaymentAttempt


class StaffCancellationMigrationTests(TransactionTestCase):
    previous = [('payments', '0002_onlinepaymentattempt_stored_processor_id_and_more')]
    target = [('payments', '0003_staff_cancellation')]

    def setUp(self):
        super().setUp()
        self.addCleanup(self.restore_schema)
        executor = MigrationExecutor(connection)
        executor.migrate(self.previous)
        self.apps = executor.loader.project_state(self.previous).apps

    def restore_schema(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def historic_attempt(self, label, **changes):
        user = self.apps.get_model('users', 'StaffUser').objects.create(username=label)
        values = dict(created_by_id=user.pk, request_key=uuid.uuid4(), request_fingerprint='f' * 64,
                      stored_member_id='GYMMSGUEST', customer_name=label, plan_label='Daily',
                      duration_days=1, amount=1, amount_centavos=100, mode='live',
                      status='cancel_requested', cancel_reason='staff')
        values.update(changes)
        return self.apps.get_model('payments', 'OnlinePaymentAttempt').objects.create(**values)

    def test_backfill_releases_only_unpaid_unresolved_staff_cancellations(self):
        cancelled = self.historic_attempt('cancelled', payment_intent_id='pi_old')
        review = self.historic_attempt('review', status='needs_review')
        active = self.historic_attempt('active', status='ready', cancel_reason='')
        expiry = self.historic_attempt('expiry', cancel_reason='expiry')
        known_receipt = self.historic_attempt('known-receipt', provider_payment_id='pay_known')
        terminal = self.historic_attempt('terminal', status='cancelled')
        ledger = self.apps.get_model('payments', 'Payment').objects.create(amount=1)
        paid = self.historic_attempt('paid', status='completed', payment_id=ledger.pk)
        member = self.apps.get_model('memberships', 'Member').objects.create(
            member_id='GYM00001', name='Unchanged', start_date='2026-10-19', end_date='2026-11-19',
            membership_fee=1, is_active=True,
        )
        MigrationExecutor(connection).migrate(self.target)

        for old in (cancelled, review, active, expiry, known_receipt, terminal, paid):
            current = OnlinePaymentAttempt.objects.get(pk=old.pk)
            released = old.pk in (cancelled.pk, review.pk)
            self.assertEqual(current.staff_cancelled_at, old.updated_at if released else None)
            self.assertEqual(current.blocks_checkout, old.status in ('ready', 'cancel_requested', 'needs_review') and not released)
            self.assertEqual(current.status, old.status)
            self.assertEqual(current.payment_intent_id, old.payment_intent_id)
            self.assertEqual(current.provider_payment_id, old.provider_payment_id)
            self.assertEqual(current.payment_id, old.payment_id)
        new_apps = MigrationExecutor(connection).loader.project_state(self.target).apps
        self.assertEqual(new_apps.get_model('payments', 'Payment').objects.count(), 1)
        self.assertEqual(new_apps.get_model('memberships', 'Member').objects.get(pk=member.pk).end_date.isoformat(), '2026-11-19')

        # The migrated old row no longer occupies the staff slot, but the new
        # active row must still exclude a second concurrent checkout.
        values = dict(created_by_id=cancelled.created_by_id, request_key=uuid.uuid4(),
                      request_fingerprint='f' * 64, stored_member_id='GYMMSGUEST', customer_name='New',
                      plan_label='Daily', duration_days=1, amount=1, amount_centavos=100, mode='live')
        OnlinePaymentAttempt.objects.create(**values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OnlinePaymentAttempt.objects.create(**dict(values, request_key=uuid.uuid4()))

        self.assertEqual(MigrationExecutor(connection).migration_plan(self.target), [])
