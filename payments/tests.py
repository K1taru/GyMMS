"""Provider fixtures never make network requests or use live credentials."""
import copy
import hashlib
import hmac
import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils import timezone
from memberships.models import Member
from payments.models import OnlinePaymentAttempt, Payment, PayMongoWebhookEvent, MembershipPricing
from payments.services.fulfillment import CheckoutError, process_cash
from payments.services.paymongo import ProviderError
from payments.services import qrph

CONFIG = dict(PAYMONGO_ENABLED=True, PAYMONGO_MODE='live',
    PAYMONGO_SECRET_KEY='sk_live_fixture_only', PAYMONGO_WEBHOOK_SECRET_TEST='test-signing-secret',
    PAYMONGO_WEBHOOK_SECRET_LIVE='live-signing-secret', PAYMONGO_QR_EXPIRY_SECONDS=1800)


class Fixtures:
    def setUp(self):
        super().setUp()
        users = get_user_model()
        self.staff = users.objects.create_user(username='staff', role='Staff')
        self.other = users.objects.create_user(username='other', role='Staff')
        self.owner = users.objects.create_user(username='owner', role='Owner')
        self.plan = MembershipPricing.objects.create(duration_days=30, duration_label='Monthly', price=500)
        today = timezone.localdate()
        self.member = Member.objects.create(member_id='GYM00001', name='Member One',
            phone_number='09123456789', address='Manila', emergency_contact='Contact',
            emergency_phone='09123456788', start_date=today, end_date=today, membership_fee=0, is_active=False)
        self.client.force_login(self.staff)

    def data(self, **changes):
        result = dict(member_id=self.member.member_id, pricing_id=str(self.plan.pk),
                      request_key=str(uuid.uuid4()), remarks='', payment_method='Cash')
        result.update(changes)
        return result

    def attempt(self, user=None, **changes):
        return qrph.create_attempt(user or self.staff, self.data(**changes))

    def provider(self, attempt, status='awaiting_next_action'):
        intent_id = attempt.payment_intent_id or 'pi_' + attempt.pk.hex
        method_id = attempt.payment_method_id or 'pm_' + attempt.pk.hex
        payment = {'id': 'pay_' + attempt.pk.hex, 'type': 'payment', 'attributes': {
            'amount': attempt.amount_centavos, 'currency': 'PHP', 'status': 'paid',
            'livemode': attempt.mode == 'live', 'payment_intent_id': intent_id,
            'paid_at': int(time.time()), 'source': {'type': 'qrph'}}}
        intent = {'id': intent_id, 'type': 'payment_intent', 'attributes': {
            'amount': attempt.amount_centavos, 'currency': 'PHP', 'livemode': attempt.mode == 'live',
            'status': status, 'payment_method_allowed': ['qrph'],
            'payments': [copy.deepcopy(payment)] if status == 'succeeded' else [],
            'next_action': {'type': 'consume_qr', 'code': {
                'image_url': 'data:image/png;base64,aGVsbG8=', 'expires_at': int(time.time()) + 1800,
                'test_url': 'https://payments.paymongo.com/test/' + attempt.pk.hex}}}}
        client = Mock()
        client.create_intent.return_value = copy.deepcopy(intent)
        client.create_method.return_value = {'id': method_id, 'type': 'payment_method',
            'attributes': {'type': 'qrph', 'livemode': attempt.mode == 'live'}}
        client.attach_method.return_value = copy.deepcopy(intent)
        client.retrieve_intent.return_value = copy.deepcopy(intent)
        client.retrieve_payment.return_value = copy.deepcopy(payment)
        client.cancel_intent.return_value = {'id': intent_id, 'type': 'payment_intent',
            'attributes': dict(intent['attributes'], status='cancelled', next_action=None)}
        return client, intent, payment

    def ready(self, attempt=None):
        attempt = attempt or self.attempt()
        client, _, _ = self.provider(attempt)
        qrph.process_attempt(attempt.pk, client=client)
        attempt.refresh_from_db()
        return attempt

    def event(self, attempt, event_id=None, payment=None, event_type='payment.paid'):
        if payment is None:
            _, _, payment = self.provider(attempt, 'succeeded')
        return {'data': {'id': event_id or 'evt_' + uuid.uuid4().hex, 'type': 'event', 'attributes': {
            'type': event_type, 'livemode': attempt.mode == 'live', 'data': payment}}}

    def signed(self, payload, mode='live', timestamp=None):
        body = json.dumps(payload, separators=(',', ':')).encode()
        timestamp = int(time.time()) if timestamp is None else timestamp
        secret = CONFIG['PAYMONGO_WEBHOOK_SECRET_' + mode.upper()]
        sig = hmac.new(secret.encode(), str(timestamp).encode() + b'.' + body, hashlib.sha256).hexdigest()
        return body, f't={timestamp},{"li" if mode == "live" else "te"}={sig}'

    def settle(self, attempt, event_id=None):
        client, _, payment = self.provider(attempt, 'succeeded')
        body, sig = self.signed(self.event(attempt, event_id, payment), attempt.mode)
        event = qrph.receive_webhook(attempt.mode, body, sig)
        qrph.process_webhook(event.pk, client=client)
        attempt.refresh_from_db()
        return attempt


@override_settings(**CONFIG)
class LifecycleTests(Fixtures, TestCase):
    def test_preparing_and_ready_never_activate_or_record_revenue(self):
        attempt = self.ready()
        self.assertEqual(attempt.status, 'ready')
        self.assertEqual(attempt.amount_centavos, 50000)
        self.assertTrue(attempt.qr_image.startswith('data:image/png;'))
        self.assertIsNotNone(attempt.expires_at)
        self.assertFalse(Payment.objects.exists())
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_same_request_retries_and_conflicting_reuse(self):
        data = self.data()
        first = qrph.create_attempt(self.staff, data)
        self.assertEqual(qrph.create_attempt(self.staff, data).pk, first.pk)
        for user, payload in [(self.other, data), (self.staff, dict(data, member_id='GYMMSGUEST')),
                              (self.staff, self.data(member_id='GYMMSGUEST', guest_name='Another'))]:
            with self.assertRaises(CheckoutError):
                qrph.create_attempt(user, payload)
        self.assertEqual(OnlinePaymentAttempt.objects.count(), 1)

    def test_disabled_feature_still_settles_existing_payment(self):
        attempt = self.ready()
        with override_settings(PAYMONGO_ENABLED=False):
            with self.assertRaises(CheckoutError):
                self.attempt(user=self.other)
            self.settle(attempt)
        self.assertEqual(Payment.objects.count(), 1)

    def test_verified_payment_activates_and_duplicate_events_settle_once(self):
        attempt = self.ready()
        for event_id in ['evt_once', 'evt_once', 'evt_another']:
            self.settle(attempt, event_id)
        self.member.refresh_from_db()
        self.assertEqual(attempt.status, 'completed')
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(PayMongoWebhookEvent.objects.count(), 2)
        self.assertTrue(self.member.is_active)
        self.assertEqual(self.member.end_date, timezone.localdate() + timedelta(days=30))
        self.assertEqual(attempt.payment.payment_method, 'QRPh')

    def test_active_renewal_and_expired_membership(self):
        for active, offset, expected in [(True, 20, 50), (True, -2, 30)]:
            self.member.is_active = active
            self.member.end_date = timezone.localdate() + timedelta(days=offset)
            self.member.save()
            self.settle(self.ready())
            self.member.refresh_from_db()
            self.assertEqual(self.member.end_date, timezone.localdate() + timedelta(days=expected))

    def test_walkin_has_receipt_and_no_membership_update(self):
        attempt = self.ready(self.attempt(member_id='GYMMSGUEST', guest_name='Guest One'))
        self.settle(attempt)
        payment = Payment.objects.get()
        self.assertIsNone(payment.member)
        self.assertEqual(payment.stored_member_id, 'GYMMSGUEST')
        self.assertEqual(payment.stored_member_name, 'Guest One')
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_plan_snapshot_survives_change_and_deletion(self):
        attempt = self.ready()
        self.plan.price, self.plan.duration_days = 900, 90
        self.plan.save()
        self.plan.delete()
        self.settle(attempt)
        receipt = Payment.objects.get()
        self.assertEqual(receipt.amount, Decimal('500'))
        self.assertEqual(receipt.stored_duration_days, 30)
        self.assertIsNone(receipt.membership_plan)

    def test_paid_deleted_member_preserves_receipt_for_review(self):
        attempt = self.ready()
        self.member.is_deleted = True
        self.member.save()
        self.settle(attempt)
        self.assertEqual(attempt.status, 'completed')
        self.assertTrue(attempt.review_required)
        self.assertEqual(Payment.objects.count(), 1)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_missed_webhook_and_late_success_after_cancel_recover(self):
        attempt = self.ready()
        attempt.status = 'cancelled'
        attempt.save()
        client, _, _ = self.provider(attempt, 'succeeded')
        qrph.reconcile_attempt(attempt.pk, client=client)
        self.settle(attempt)
        self.assertEqual(Payment.objects.count(), 1)

    def test_wrong_evidence_never_settles(self):
        for field, value in [('amount', 100), ('currency', 'USD'), ('livemode', False),
                             ('payment_intent_id', 'pi_wrong')]:
            with self.subTest(field=field):
                OnlinePaymentAttempt.objects.all().delete()
                attempt = self.ready()
                client, _, payment = self.provider(attempt, 'succeeded')
                payment['attributes'][field] = value
                client.retrieve_payment.return_value = payment
                body, sig = self.signed(self.event(attempt, payment=payment))
                event = qrph.receive_webhook('live', body, sig)
                qrph.process_webhook(event.pk, client=client)
                self.assertFalse(Payment.objects.exists())

    def test_unknown_creation_timeout_is_not_repeated(self):
        attempt = self.attempt()
        client, _, _ = self.provider(attempt)
        client.create_intent.side_effect = ProviderError(uncertain=True)
        qrph.process_attempt(attempt.pk, client=client)
        qrph.process_attempt(attempt.pk, client=client)
        self.assertEqual(client.create_intent.call_count, 1)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'needs_review')

    def test_cash_idempotency_and_digital_bypass_rejection(self):
        data = self.data()
        first, _ = process_cash(self.staff, data)
        again, _ = process_cash(self.staff, data)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(Payment.objects.count(), 1)
        for method in ['GCash', 'Maya', 'GoTyme', 'QRPh', 'PayPal', 'Credit Card']:
            with self.assertRaises(CheckoutError):
                process_cash(self.staff, self.data(payment_method=method))

    def test_pending_qr_blocks_cash(self):
        self.ready()
        with self.assertRaises(CheckoutError):
            process_cash(self.other, self.data())
        self.assertFalse(Payment.objects.exists())

    def test_cash_failure_rolls_back_and_uses_manila_date(self):
        with patch('payments.services.fulfillment.fulfill_member', side_effect=RuntimeError('retry')):
            with self.assertRaises(RuntimeError):
                process_cash(self.staff, self.data())
        self.assertFalse(Payment.objects.exists())
        fixed = datetime(2026, 10, 13, 17, 0, tzinfo=dt_timezone.utc)
        with patch('django.utils.timezone.now', return_value=fixed):
            _, end = process_cash(self.staff, self.data())
        self.assertEqual(end.isoformat(), '2026-11-13')

    def test_test_simulator_never_changes_membership_or_revenue(self):
        with override_settings(PAYMONGO_MODE='test', PAYMONGO_SECRET_KEY='sk_test_fixture'):
            attempt = self.settle(self.ready())
        self.assertEqual(attempt.status, 'completed')
        self.assertFalse(Payment.objects.exists())
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_cancel_does_not_release_until_provider_confirms(self):
        attempt = self.ready()
        qrph.request_cancel(attempt.pk)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'cancel_requested')
        self.assertTrue(attempt.is_unresolved)
        client, _, _ = self.provider(attempt)
        qrph.reconcile_attempt(attempt.pk, client=client)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'cancelled')
        self.assertFalse(attempt.is_unresolved)
        self.assertFalse(Payment.objects.exists())

    def test_processing_payment_wins_cancellation_race(self):
        attempt = self.ready()
        qrph.request_cancel(attempt.pk)
        attempt.refresh_from_db()
        client, _, _ = self.provider(attempt, 'processing')
        qrph.reconcile_attempt(attempt.pk, client=client)
        client.cancel_intent.assert_not_called()
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'cancel_requested')
        self.settle(attempt)
        self.assertEqual(attempt.status, 'completed')
        self.assertEqual(Payment.objects.count(), 1)

    def test_expired_provider_qr_unblocks_even_if_cancel_api_rejects(self):
        attempt = self.ready()
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save()
        qrph.request_cancel(attempt.pk)
        attempt.refresh_from_db()
        client, intent, _ = self.provider(attempt, 'awaiting_payment_method')
        intent['attributes']['next_action'] = None
        client.retrieve_intent.return_value = intent
        client.cancel_intent.side_effect = ProviderError(retryable=False)
        qrph.reconcile_attempt(attempt.pk, client=client)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'expired')
        self.assertFalse(attempt.is_unresolved)
        client.cancel_intent.assert_not_called()

    def test_transient_verification_failure_retains_cancellation(self):
        attempt = self.ready()
        qrph.request_cancel(attempt.pk)
        client, _, _ = self.provider(attempt)
        client.retrieve_intent.side_effect = ProviderError()
        qrph.reconcile_attempt(attempt.pk, client=client)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'cancel_requested')
        self.assertGreater(attempt.retry_count, 0)

    def test_disabled_worker_still_processes_existing_due_payment(self):
        attempt = self.ready()
        OnlinePaymentAttempt.objects.filter(pk=attempt.pk).update(next_retry_at=timezone.now())
        client, _, _ = self.provider(attempt, 'succeeded')
        with override_settings(PAYMONGO_ENABLED=False):
            self.assertGreater(qrph.worker_tick(client=client), 0)
        self.assertEqual(Payment.objects.count(), 1)

    def test_old_paid_deleted_member_does_not_conflict_with_new_checkout(self):
        old = self.ready()
        old.status = 'cancelled'
        old.save()
        new = self.attempt(member_id='GYMMSGUEST', guest_name='Next Customer')
        self.member.is_deleted = True
        self.member.save()
        self.settle(old)
        new.refresh_from_db()
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(old.status, 'completed')
        self.assertTrue(old.review_required)
        self.assertEqual(new.status, 'preparing')

    def test_stale_failure_notification_cannot_reopen_paid_checkout(self):
        attempt = self.settle(self.ready())
        client, _, payment = self.provider(attempt, 'succeeded')
        payment['attributes']['status'] = 'failed'
        body, sig = self.signed(self.event(attempt, payment=payment, event_type='payment.failed'))
        event = qrph.receive_webhook('live', body, sig)
        qrph.process_webhook(event.pk, client=client)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'completed')
        self.assertEqual(Payment.objects.count(), 1)

    def test_unconfigured_provider_does_not_create_pending_checkout(self):
        with override_settings(PAYMONGO_SECRET_KEY=''):
            with self.assertRaises(CheckoutError):
                self.attempt()
        self.assertFalse(OnlinePaymentAttempt.objects.exists())

    def test_snapshots_cannot_be_modified_after_creation(self):
        attempt = self.attempt()
        attempt.amount = Decimal('1')
        with self.assertRaises((ValueError, CheckoutError)):
            attempt.save()


@override_settings(**CONFIG)
class EndpointTests(Fixtures, TestCase):
    def test_create_resume_permissions_and_csrf(self):
        response = self.client.post('/payments/qrph/attempts/', self.data())
        self.assertEqual(response.status_code, 202)
        pk = response.json()['attempt']['id']
        self.assertEqual(self.client.get('/payments/qrph/current/').json()['attempt']['id'], pk)
        self.client.force_login(self.other)
        self.assertIn(self.client.get(f'/payments/qrph/attempts/{pk}/').status_code, [403, 404])
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(f'/payments/qrph/attempts/{pk}/').status_code, 200)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)
        self.assertEqual(csrf_client.post('/payments/qrph/attempts/', self.data()).status_code, 403)

    def test_unauthenticated_and_nonstaff_rejected(self):
        self.client.logout()
        self.assertIn(self.client.post('/payments/qrph/attempts/', self.data()).status_code, [401, 302])
        user = get_user_model().objects.create_user(username='wrong-role', role='Customer')
        self.client.force_login(user)
        self.assertEqual(self.client.post('/payments/qrph/attempts/', self.data()).status_code, 403)

    def test_webhook_deduplicates_without_synchronous_settlement(self):
        attempt = self.ready()
        body, sig = self.signed(self.event(attempt, 'evt_once'))
        for _ in range(2):
            response = self.client.post('/payments/webhooks/paymongo/live/', body,
                content_type='application/json', HTTP_PAYMONGO_SIGNATURE=sig)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(PayMongoWebhookEvent.objects.count(), 1)
        self.assertFalse(Payment.objects.exists())

    def test_tampered_wrong_mode_or_stale_signature_rejected(self):
        payload = self.event(self.ready())
        body, sig = self.signed(payload)
        cases = [(body + b' ', sig, 'live'), (body, sig, 'test'),
                 (*self.signed(payload, timestamp=int(time.time()) - 1000), 'live')]
        for body, sig, mode in cases:
            response = self.client.post(f'/payments/webhooks/paymongo/{mode}/', body,
                content_type='application/json', HTTP_PAYMONGO_SIGNATURE=sig)
            self.assertGreaterEqual(response.status_code, 400)
        self.assertFalse(PayMongoWebhookEvent.objects.exists())

    def test_manual_digital_rejected_and_revenue_excludes_failed_history(self):
        response = self.client.post('/payments/process/', self.data(payment_method='GCash', reference_number='fake'))
        self.assertEqual(response.status_code, 400)
        process_cash(self.staff, self.data())
        Payment.objects.create(amount=900, payment_method='PayPal', status='Failed')
        response = self.client.get('/payments/transactions/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_revenue'], 500)

    def test_widget_is_on_all_authenticated_sections(self):
        for url in ['/payments/', '/memberships/', '/dashboard/', '/metrics/', '/users/profile/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'qr_payment.js')


@override_settings(**CONFIG)
class PostgreSQLConcurrencyTests(Fixtures, TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_simultaneous_cash_retries_create_one_receipt(self):
        data = self.data()
        barrier = threading.Barrier(2)
        def pay(_):
            close_old_connections()
            try:
                user = get_user_model().objects.get(pk=self.staff.pk)
                barrier.wait(timeout=10)
                return process_cash(user, data)[0].pk
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(pay, range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(Payment.objects.count(), 1)

    @skipUnlessDBFeature('has_select_for_update')
    def test_concurrent_independent_renewals_keep_both_extensions(self):
        old_end = timezone.localdate() + timedelta(days=10)
        self.member.is_active, self.member.end_date = True, old_end
        self.member.save()
        first = self.ready()
        # Provider already received first payment; simulate a second independent
        # purchase without violating the one-unresolved-member checkout rule.
        first.status = 'expired'
        first.save()
        second = self.ready(self.attempt(user=self.other))
        barrier = threading.Barrier(2)
        def settle(attempt):
            close_old_connections()
            try:
                client, _, payment = self.provider(attempt, 'succeeded')
                body, sig = self.signed(self.event(attempt, payment=payment))
                event = qrph.receive_webhook('live', body, sig)
                barrier.wait(timeout=10)
                qrph.process_webhook(event.pk, client=client)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(settle, [first, second]))
        self.member.refresh_from_db()
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(self.member.end_date, old_end + timedelta(days=60))
