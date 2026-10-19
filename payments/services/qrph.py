"""Durable QRPh checkout, verified webhooks and recoverable worker jobs."""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone
from urllib.parse import urlparse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from memberships.models import Member
from payments.models import OnlinePaymentAttempt, PayMongoWebhookEvent, Payment, UNRESOLVED_STATUSES
from .fulfillment import CheckoutError, checkout_snapshot, request_uuid, request_fingerprint, fulfill_member, serialize_payment
from .paymongo import PayMongoClient, ProviderError


def enabled():
    return bool(getattr(settings, 'PAYMONGO_ENABLED', False))


@transaction.atomic
def create_attempt(user, data):
    if not enabled():
        raise CheckoutError('QRPh payments are not configured.', 503)
    mode = getattr(settings, 'PAYMONGO_MODE', 'test')
    if mode not in ('test', 'live'):
        raise CheckoutError('QRPh payments are not configured.', 503)
    secret_key = getattr(settings, 'PAYMONGO_SECRET_KEY_' + mode.upper(), '') or getattr(settings, 'PAYMONGO_SECRET_KEY', '')
    webhook_secret = getattr(settings, 'PAYMONGO_WEBHOOK_SECRET_' + mode.upper(), '')
    if not secret_key.startswith('sk_' + mode + '_') or not webhook_secret:
        raise CheckoutError('QRPh payments are not configured for this mode.', 503)
    key = request_uuid(data)
    fingerprint = request_fingerprint(data)
    get_user_model().objects.select_for_update().get(pk=user.pk)
    existing = OnlinePaymentAttempt.objects.filter(request_key=key).first()
    if existing:
        if existing.created_by_id != user.pk or existing.request_fingerprint != fingerprint:
            raise CheckoutError('Request key was already used for a different payment.', 409)
        return existing
    if OnlinePaymentAttempt.objects.filter(created_by=user, status__in=UNRESOLVED_STATUSES).exists():
        raise CheckoutError('Resolve your current QRPh payment before starting another.', 409)
    member, pricing, name, remarks = checkout_snapshot(data)
    if pricing.price < 1:
        raise CheckoutError('QR Ph requires a minimum payment of PHP 1.00.')
    if member and OnlinePaymentAttempt.objects.filter(member=member, status__in=UNRESOLVED_STATUSES).exists():
        raise CheckoutError('This member already has an unresolved QRPh payment.', 409)
    return OnlinePaymentAttempt.objects.create(
        request_key=key, request_fingerprint=fingerprint, created_by=user, member=member, membership_plan=pricing,
        stored_member_id=member.member_id if member else 'GYMMSGUEST', customer_name=name,
        plan_label=pricing.duration_label, duration_days=pricing.duration_days,
        amount=pricing.price, amount_centavos=int(pricing.price * 100), remarks=remarks, mode=mode,
        message='Preparing your QRPh payment.')


def serialize_attempt(attempt):
    result = {'id': str(attempt.pk), 'status': attempt.status, 'is_unresolved': attempt.is_unresolved,
              'review_required': attempt.review_required,
              'member_id': attempt.stored_member_id, 'customer_name': attempt.customer_name,
              'plan_label': attempt.plan_label, 'amount': str(attempt.amount), 'currency': attempt.currency,
              'qr_image': attempt.qr_image, 'expires_at': attempt.expires_at.isoformat() if attempt.expires_at else None,
              'server_time': timezone.now().isoformat(), 'message': attempt.message,
              'payment': serialize_payment(attempt.payment) if attempt.payment_id else None,
              'new_end_date': attempt.new_end_date.isoformat() if attempt.new_end_date else None,
              'is_walkin': attempt.is_walkin, 'test_mode': attempt.mode == 'test',
              'can_cancel': attempt.is_unresolved and not attempt.payment_id and not attempt.provider_payment_id}
    if attempt.mode == 'test' and attempt.test_url:
        result['test_url'] = attempt.test_url
    return result


@transaction.atomic
def request_cancel(attempt_id):
    attempt = OnlinePaymentAttempt.objects.select_for_update().get(pk=attempt_id)
    if attempt.is_unresolved and not attempt.payment_id:
        attempt.status = 'cancel_requested'
        attempt.cancel_reason = 'staff'
        attempt.message = 'Checking payment status and requesting provider cancellation.'
        attempt.next_retry_at = timezone.now()
        attempt.save(update_fields=['status', 'cancel_reason', 'message', 'next_retry_at', 'updated_at'])
    return attempt


def receive_webhook(mode, raw_body, signature):
    if mode not in ('test', 'live'):
        raise CheckoutError('Invalid webhook mode.', 404)
    secret = getattr(settings, 'PAYMONGO_WEBHOOK_SECRET_' + mode.upper(), '')
    if not secret:
        raise CheckoutError('Webhook is not configured.', 503)
    try:
        parts = {}
        for item in signature.split(','):
            key, value = item.strip().split('=', 1)
            if key in parts:
                raise ValueError()
            parts[key] = value
        timestamp = int(parts['t'])
        signed = parts['t'].encode() + b'.' + raw_body
        expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        if abs(timezone.now().timestamp() - timestamp) > getattr(settings, 'PAYMONGO_WEBHOOK_TOLERANCE_SECONDS', 300):
            raise ValueError()
        if not hmac.compare_digest(expected, parts['te' if mode == 'test' else 'li']):
            raise ValueError()
        payload = json.loads(raw_body)
        event = payload['data']
        attrs = event['attributes']
        if event['type'] != 'event' or not isinstance(event['id'], str) or not event['id'] or len(event['id']) > 100:
            raise ValueError()
        if attrs['livemode'] is not (mode == 'live') or not isinstance(attrs['type'], str) or len(attrs['type']) > 100:
            raise ValueError()
        if not isinstance(attrs['data'], dict):
            raise ValueError()
    except (KeyError, TypeError, ValueError, AttributeError, UnicodeDecodeError):
        raise CheckoutError('Invalid webhook signature or payload.', 400)
    event, _ = PayMongoWebhookEvent.objects.get_or_create(mode=mode, event_id=event['id'], defaults={
        'event_type': attrs['type'], 'payload': payload})
    return event


def _claim(model, pk):
    with transaction.atomic():
        obj = model.objects.select_for_update().get(pk=pk)
        now = timezone.now()
        if obj.locked_until and obj.locked_until > now:
            return None
        if isinstance(obj, PayMongoWebhookEvent) and obj.status == 'processed':
            return None
        obj.work_token = uuid.uuid4()
        obj.locked_until = now + timedelta(seconds=180)
        obj.save(update_fields=['work_token', 'locked_until'])
        return obj


def _save(attempt, **values):
    # Lock the row for the state decision so a simultaneous cancel cannot be overwritten.
    with transaction.atomic():
        current = OnlinePaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        if current.work_token != attempt.work_token or not current.locked_until or current.locked_until <= timezone.now():
            raise ProviderError('Worker claim expired.')
        values['updated_at'] = timezone.now()
        incoming_status = values.get('status')
        if incoming_status == 'needs_review':
            values['review_required'] = True
            if current.status not in UNRESOLVED_STATUSES:
                values['status'] = current.status
        if incoming_status in ('ready', 'processing', 'preparing', 'needs_review') and current.status == 'cancel_requested':
            values['status'] = 'cancel_requested'
            if incoming_status != 'needs_review':
                values['message'] = current.message
        OnlinePaymentAttempt.objects.filter(pk=attempt.pk, work_token=attempt.work_token).update(**values)
        for key, value in values.items():
            setattr(attempt, key, value)


def _review(attempt, message):
    try:
        _save(attempt, status='needs_review', message=message)
    except ProviderError:
        # A lost lease belongs to the replacement worker; never overwrite its result.
        return


def _check_mode(resource, attempt, resource_type):
    if not isinstance(resource, dict) or not isinstance(resource.get('attributes'), dict):
        raise ProviderError('Malformed provider resource.', retryable=False)
    attrs = resource['attributes']
    if resource.get('type') != resource_type or attrs.get('livemode') is not (attempt.mode == 'live'):
        raise ProviderError('Provider resource identity or mode does not match checkout.', retryable=False)
    return attrs


def _intent_attrs(resource, attempt):
    attrs = _check_mode(resource, attempt, 'payment_intent')
    if (resource.get('id') != attempt.payment_intent_id or attrs.get('amount') != attempt.amount_centavos
            or attrs.get('currency') != attempt.currency or 'qrph' not in attrs.get('payment_method_allowed', [])):
        raise ProviderError('Provider intent does not match checkout.', retryable=False)
    return attrs


def _validated_test_url(value):
    if not isinstance(value, str):
        return ''
    parsed = urlparse(value)
    if parsed.scheme == 'https' and parsed.hostname in ('payments.paymongo.com', 'test-payments.paymongo.com') and not parsed.username and not parsed.password:
        return value
    return ''


def _apply_intent(attempt, resource, client):
    attrs = _intent_attrs(resource, attempt)
    status = attrs.get('status')
    if status == 'succeeded':
        payments = attrs.get('payments') or []
        if not payments:
            _review(attempt, 'Provider reports success without a payment receipt. Owner review is required.')
            return
        payment_id = payments[-1].get('id')
        _settle(attempt, client.retrieve_payment(payment_id), expected_payment_id=payment_id)
        return
    # A verified simulated receipt is terminal too, even without a ledger row.
    if attempt.payment_id or (attempt.status == 'completed' and attempt.provider_payment_id):
        return
    if status in ('cancelled', 'canceled'):
        _save(attempt, status='expired' if attempt.cancel_reason == 'expiry' else 'cancelled', pending_operation='', retry_count=0, message='Provider confirmed QR expiry.' if attempt.cancel_reason == 'expiry' else 'Provider confirmed cancellation.')
    elif status == 'awaiting_next_action':
        action = attrs.get('next_action') or {}
        code = action.get('code') or {}
        image = code.get('image_url', '')
        if not isinstance(image, str) or not image.startswith('data:image/'):
            _review(attempt, 'Provider did not return a valid QR image. Owner review is required.')
            return
        expiry = code.get('expires_at') or action.get('expires_at')
        expires_at = attempt.expires_at
        if isinstance(expiry, (int, float)):
            expires_at = datetime.fromtimestamp(expiry, datetime_timezone.utc)
        if expires_at is None:
            expires_at = timezone.now() + timedelta(seconds=getattr(settings, 'PAYMONGO_QR_EXPIRY_SECONDS', 1800))
        _save(attempt, status='cancel_requested' if attempt.status == 'cancel_requested' else 'ready',
              qr_image=image, expires_at=expires_at, pending_operation='', retry_count=0,
              test_url=_validated_test_url(code.get('test_url') or action.get('redirect', {}).get('url')) if attempt.mode == 'test' else '',
              message='Scan the QR code with a participating banking or e-wallet app.' if attempt.status != 'cancel_requested' else attempt.message)
    elif status == 'processing':
        _save(attempt, status='cancel_requested' if attempt.status == 'cancel_requested' else 'processing',
              message='The provider is processing the payment.')
    elif status == 'awaiting_payment_method':
        last_error = attrs.get('last_payment_error') or {}
        expired = (attempt.qr_image and attempt.expires_at and attempt.expires_at <= timezone.now()) or last_error.get('code') in ('qrph_expired', 'qrph.expired')
        if not attempt.pending_operation and attempt.payment_method_id and expired:
            _save(attempt, status='expired', retry_count=0, message='Provider confirmed this QR is no longer payable.')
        elif not attempt.pending_operation and attempt.qr_image and last_error:
            _save(attempt, status='failed', retry_count=0, message='Provider confirmed payment failure.')
        elif attempt.payment_method_id or attempt.pending_operation:
            _review(attempt, 'Provider could not confirm this payment. Owner review is required.')
    else:
        _review(attempt, 'Provider returned an unexpected payment state. Owner review is required.')


def _settle(attempt, resource, expected_payment_id=None):
    attrs = _check_mode(resource, attempt, 'payment')
    source = attrs.get('source') or {}
    if not isinstance(source, dict):
        raise ProviderError('Malformed provider source.', retryable=False)
    payment_id = resource.get('id')
    if (not payment_id or (expected_payment_id is not None and payment_id != expected_payment_id) or attrs.get('status') != 'paid' or attrs.get('amount') != attempt.amount_centavos
            or attrs.get('currency') != attempt.currency or attrs.get('payment_intent_id') != attempt.payment_intent_id
            or source.get('type') != 'qrph'):
        raise ProviderError('Provider payment receipt does not match checkout.', retryable=False)
    with transaction.atomic():
        locked = OnlinePaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        if locked.work_token != attempt.work_token or not locked.locked_until or locked.locked_until <= timezone.now():
            raise ProviderError('Worker claim expired.')
        if locked.mode == 'test':
            if locked.status == 'completed':
                if locked.provider_payment_id != payment_id:
                    _review(attempt, 'Multiple simulated receipts require owner review.')
                return
            locked.provider_payment_id = payment_id
            locked.status = 'completed'
            locked.pending_operation = ''
            locked.retry_count = 0
            locked.message = 'Test payment simulated; no membership or revenue recorded.'
            locked.save()
            attempt.refresh_from_db()
            return
        if locked.payment_id:
            if locked.provider_payment_id != payment_id:
                _review(attempt, 'Multiple paid receipts require owner review.')
            return
        member = Member.objects.select_for_update().filter(pk=locked.member_id).first() if locked.member_id else None
        requires_review = not locked.is_walkin and (member is None or member.is_deleted)
        end_date = None if requires_review else fulfill_member(member, locked.duration_days, locked.amount)
        paid_at = attrs.get('paid_at')
        payment_date = datetime.fromtimestamp(paid_at, datetime_timezone.utc) if isinstance(paid_at, (int, float)) else timezone.now()
        payment = Payment.objects.create(member=member, stored_member_id=locked.stored_member_id,
            stored_member_name=locked.customer_name, membership_plan=locked.membership_plan,
            stored_plan_label=locked.plan_label, stored_duration_days=locked.duration_days, amount=locked.amount,
            payment_method='QRPh', reference_number=payment_id, payment_date=payment_date,
            status='Completed', processed_by=locked.created_by, remarks=locked.remarks)
        locked.payment = payment
        locked.provider_payment_id = payment_id
        locked.new_end_date = end_date
        locked.pending_operation = ''
        locked.retry_count = 0
        # A confirmed receipt is terminal even when fulfillment requires manual review.
        # Keeping a paid late receipt unresolved could violate a newer staff checkout's slot.
        locked.status = 'completed'
        locked.review_required = requires_review
        locked.message = 'Payment received; deleted member requires owner review.' if requires_review else 'Payment confirmed successfully.'
        locked.save()
        attempt.refresh_from_db()


def _mutation(attempt, operation, callback):
    _save(attempt, pending_operation=operation)
    try:
        return callback()
    except ProviderError as exc:
        if not exc.uncertain:
            _save(attempt, pending_operation='')
        raise


def process_attempt(attempt_id, client=None):
    attempt = _claim(OnlinePaymentAttempt, attempt_id)
    if not attempt:
        return
    try:
        client = client or PayMongoClient(attempt.mode)
        if attempt.payment_intent_id and (attempt.pending_operation or attempt.status != 'preparing'):
            _reconcile(attempt, client)
            return
        if attempt.pending_operation:
            _review(attempt, 'Provider request outcome is unknown. Owner review is required; do not collect another payment.')
            return
        if attempt.status == 'cancel_requested' and not attempt.payment_intent_id:
            _save(attempt, status='cancelled', message='Checkout cancelled before creating a provider payment.')
            return
        if attempt.status != 'preparing':
            return
        if not attempt.payment_intent_id:
            resource = _mutation(attempt, 'create_intent', lambda: client.create_intent(attempt))
            intent_id = resource.get('id')
            if not intent_id:
                raise ProviderError('Missing provider intent identifier.', uncertain=True)
            _save(attempt, payment_intent_id=intent_id, pending_operation='')
            _intent_attrs(resource, attempt)
        if not attempt.payment_method_id:
            resource = _mutation(attempt, 'create_method', lambda: client.create_method(attempt))
            if not resource.get('id'):
                raise ProviderError('Missing provider method identifier.', uncertain=True)
            _save(attempt, payment_method_id=resource['id'], pending_operation='')
            attrs = _check_mode(resource, attempt, 'payment_method')
            if attrs.get('type') != 'qrph':
                raise ProviderError('Provider method does not match QRPh.', retryable=False)
        # Cancellation can be requested while the network call is running.
        latest = OnlinePaymentAttempt.objects.get(pk=attempt.pk)
        if latest.status == 'cancel_requested':
            attempt.status = latest.status
            _reconcile(attempt, client)
            return
        resource = _mutation(attempt, 'attach_method', lambda: client.attach_method(attempt.payment_intent_id, attempt.payment_method_id))
        latest = OnlinePaymentAttempt.objects.get(pk=attempt.pk)
        if latest.status == 'cancel_requested':
            attempt.status = latest.status
        _apply_intent(attempt, resource, client)
    except ProviderError as exc:
        _handle_provider_error(attempt, exc)
    except (ValueError, TypeError, KeyError, AttributeError, IntegrityError):
        _review(attempt, 'Payment status could not be confirmed. Owner review is required; do not collect another payment.')
    finally:
        _release(attempt)


def _reconcile(attempt, client):
    if not attempt.payment_intent_id:
        if attempt.pending_operation:
            _review(attempt, 'Provider creation outcome is unknown. Owner review is required.')
        elif attempt.status == 'cancel_requested':
            _save(attempt, status='cancelled', message='Checkout cancelled.')
        return
    resource = client.retrieve_intent(attempt.payment_intent_id)
    attrs = _intent_attrs(resource, attempt)
    if attrs.get('status') == 'succeeded':
        _apply_intent(attempt, resource, client)
        return
    latest = OnlinePaymentAttempt.objects.get(pk=attempt.pk)
    if latest.status == 'cancel_requested':
        attempt.status = latest.status
        attempt.cancel_reason = latest.cancel_reason
    if attempt.status != 'cancel_requested' and attrs.get('status') == 'awaiting_next_action' and attempt.expires_at and attempt.expires_at <= timezone.now():
        _save(attempt, status='cancel_requested', cancel_reason='expiry', message='QR countdown ended; confirming provider cancellation.')
    if attempt.status == 'cancel_requested':
        if attrs.get('status') == 'awaiting_payment_method' and not attempt.pending_operation:
            _apply_intent(attempt, resource, client)
            if attempt.status in ('expired', 'failed'):
                return
        if attrs.get('status') not in ('cancelled', 'canceled'):
            # Re-read after an unknown cancellation; safe only if intent remains cancelable.
            if attrs.get('status') == 'processing':
                _save(attempt, message='Payment is processing. Waiting for provider confirmation before cancellation.')
                return
            resource = _mutation(attempt, 'cancel_intent', lambda: client.cancel_intent(attempt.payment_intent_id))
        _apply_intent(attempt, resource, client)
        return
    if attempt.pending_operation in ('create_method', 'attach_method') and attrs.get('status') == 'awaiting_payment_method':
        _review(attempt, 'Provider request outcome is unknown. Cancel this checkout or request owner review.')
        return
    _apply_intent(attempt, resource, client)


def _release(attempt):
    interval = getattr(settings, 'PAYMONGO_RECONCILE_INTERVAL', 60)
    interval = min(3600, interval * (2 ** min(attempt.retry_count, 6)))
    OnlinePaymentAttempt.objects.filter(pk=attempt.pk, work_token=attempt.work_token).update(
        locked_until=None, work_token=None, next_retry_at=timezone.now() + timedelta(seconds=interval))


def _handle_provider_error(attempt, exc):
    if not OnlinePaymentAttempt.objects.filter(pk=attempt.pk, work_token=attempt.work_token, locked_until__gt=timezone.now()).exists():
        return
    _save(attempt, retry_count=attempt.retry_count + 1)
    if attempt.pending_operation or not exc.retryable:
        if not attempt.payment_intent_id and not attempt.pending_operation:
            _save(attempt, status='failed', message='Provider rejected checkout creation. No payable QR was created.')
        else:
            _review(attempt, 'Payment status could not be confirmed. Owner review is required; do not collect another payment.')
    else:
        _save(attempt, message='Provider temporarily unavailable. Retrying verification; do not collect another payment.')


def reconcile_attempt(attempt_id, client=None):
    attempt = _claim(OnlinePaymentAttempt, attempt_id)
    if not attempt:
        return
    try:
        _reconcile(attempt, client or PayMongoClient(attempt.mode))
    except ProviderError as exc:
        _handle_provider_error(attempt, exc)
    except (ValueError, TypeError, KeyError, AttributeError, IntegrityError):
        _review(attempt, 'Payment status could not be confirmed. Owner review is required; do not collect another payment.')
    finally:
        _release(attempt)


def process_webhook(event_id, client=None):
    event = _claim(PayMongoWebhookEvent, event_id)
    if not event:
        return
    try:
        data = event.payload['data']['attributes']['data']
        attrs = data.get('attributes') or {}
        intent_id = attrs.get('payment_intent_id') or (data.get('id') if data.get('type') == 'payment_intent' else '')
        method_id = attrs.get('payment_method_id') or (data.get('id') if data.get('type') == 'payment_method' else '')
        attempts = OnlinePaymentAttempt.objects.filter(mode=event.mode)
        attempt = attempts.filter(payment_intent_id=intent_id).first() if intent_id else None
        if not attempt and method_id:
            attempt = attempts.filter(payment_method_id=method_id).first()
        supported = event.event_type in ('payment.paid', 'payment.failed', 'qrph.expired', 'payment_intent.succeeded', 'payment_intent.payment_failed', 'payment_intent.awaiting_payment_method')
        if not supported:
            _finish_event(event)
            return
        if not attempt:
            raise ProviderError('No matching local checkout yet.')
        attempt = _claim(OnlinePaymentAttempt, attempt.pk)
        if not attempt:
            raise ProviderError('Checkout is being reconciled.')
        try:
            client = client or PayMongoClient(attempt.mode)
            if event.event_type == 'payment.paid':
                # Webhook is a notification; retrieve both authoritative resources independently.
                intent = client.retrieve_intent(attempt.payment_intent_id)
                intent_attrs = _intent_attrs(intent, attempt)
                if intent_attrs.get('status') != 'succeeded':
                    raise ProviderError('Provider intent has not succeeded yet.')
                _settle(attempt, client.retrieve_payment(data['id']), expected_payment_id=data['id'])
            else:
                _reconcile(attempt, client)
                if event.event_type == 'qrph.expired' and attempt.status == 'ready':
                    # A signed event alone cannot release a payment that still appears payable.
                    _save(attempt, status='cancel_requested', cancel_reason='expiry', message='QR expired; confirming provider cancellation.', next_retry_at=timezone.now())
        except ProviderError as exc:
            _handle_provider_error(attempt, exc)
            raise
        finally:
            _release(attempt)
        _finish_event(event)
    except (ProviderError, KeyError, ValueError, TypeError, AttributeError, IntegrityError):
        count = event.retry_count + 1
        PayMongoWebhookEvent.objects.filter(pk=event.pk, work_token=event.work_token).update(
            status='pending', retry_count=count, next_retry_at=timezone.now() + timedelta(seconds=min(3600, 2 ** min(count, 11))),
            locked_until=None, work_token=None, last_error='Awaiting verified provider reconciliation.')


def _finish_event(event):
    PayMongoWebhookEvent.objects.filter(pk=event.pk, work_token=event.work_token).update(
        status='processed', processed_at=timezone.now(), locked_until=None, work_token=None, last_error='')


def worker_tick(client=None, stop_requested=None):
    now = timezone.now()
    available = Q(locked_until__isnull=True) | Q(locked_until__lte=now)
    event_ids = list(PayMongoWebhookEvent.objects.filter(available, status='pending', next_retry_at__lte=now)
                     .order_by('received_at').values_list('pk', flat=True)[:20])
    for pk in event_ids:
        if stop_requested and stop_requested():
            return
        process_webhook(pk, client)
    # Keep terminal provider intents in reconciliation: a late paid receipt still settles exactly once.
    ids = list(OnlinePaymentAttempt.objects.filter(available, next_retry_at__lte=now, payment__isnull=True)
               .filter(Q(status__in=UNRESOLVED_STATUSES) | ~Q(payment_intent_id=''))
               .exclude(mode='test', status='completed')
               .order_by('next_retry_at').values_list('pk', flat=True)[:20])
    for pk in ids:
        if stop_requested and stop_requested():
            return
        process_attempt(pk, client)
    return len(event_ids) + len(ids)
