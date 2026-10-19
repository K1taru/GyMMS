"""Atomic membership fulfillment shared by Cash and verified QRPh receipts."""
import hashlib
import json
import uuid
from datetime import timedelta
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from memberships.models import Member
from payments.models import Payment, MembershipPricing, CashPaymentRequest, OnlinePaymentAttempt


class CheckoutError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def fulfill_member(member, duration_days, amount):
    """Caller holds member's row lock and surrounding transaction."""
    if member is None:
        return None
    if member.is_deleted:
        raise CheckoutError('Member is deleted; fulfillment requires owner review.', 409)
    today = timezone.localdate()
    if not member.is_active or member.end_date < today:
        member.start_date = today
        member.end_date = today + timedelta(days=duration_days)
    else:
        member.end_date += timedelta(days=duration_days)
    member.membership_fee = amount
    member.is_active = True
    member.save(update_fields=['start_date', 'end_date', 'membership_fee', 'is_active'])
    return member.end_date


def checkout_snapshot(data, lock_member=True):
    member_id = str(data.get('member_id', '')).strip()
    is_walkin = member_id == 'GYMMSGUEST'
    member = None
    if not is_walkin:
        qs = Member.objects.select_for_update() if lock_member else Member.objects
        member = qs.filter(member_id=member_id, is_deleted=False).first()
        if not member:
            raise CheckoutError('Member not found.', 404)
    try:
        pricing_id = int(data.get('pricing_id', ''))
    except (TypeError, ValueError):
        raise CheckoutError('Invalid pricing option.')
    pricing = MembershipPricing.objects.select_for_update().filter(pk=pricing_id, is_active=True).first()
    if not pricing or pricing.price <= 0 or pricing.duration_days <= 0:
        raise CheckoutError('Invalid pricing option.')
    cents = pricing.price * 100
    if cents != cents.to_integral_value():
        raise CheckoutError('Pricing must use whole centavos.')
    name = str(data.get('guest_name', 'Walk-in Guest')).strip() if is_walkin else member.name
    if not name or len(name) > 150:
        raise CheckoutError('Customer name must contain 1 to 150 characters.')
    remarks = str(data.get('remarks', '')).strip()
    if len(remarks) > 4000:
        raise CheckoutError('Remarks are too long.')
    return member, pricing, name, remarks


def request_uuid(data):
    try:
        return uuid.UUID(str(data.get('request_key', '')))
    except (TypeError, ValueError, AttributeError):
        raise CheckoutError('A UUID request_key is required.')


def request_fingerprint(data):
    return hashlib.sha256(json.dumps({k: str(data.get(k, '')).strip() for k in
                                     ('member_id', 'pricing_id', 'guest_name', 'remarks')},
                                    sort_keys=True).encode()).hexdigest()


@transaction.atomic
def process_cash(user, data):
    if data.get('payment_method') != 'Cash':
        raise CheckoutError('Manual processing only accepts Cash. Use QRPh for digital payments.')
    key = request_uuid(data)
    # Serialize all operations for this staff user, including Cash retries.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    fingerprint = request_fingerprint(data)
    existing = CashPaymentRequest.objects.filter(request_key=key).select_related('payment').first()
    if existing:
        if existing.created_by_id != user.pk or existing.fingerprint != fingerprint:
            raise CheckoutError('Request key was already used for a different payment.', 409)
        return existing.payment, existing.new_end_date
    if OnlinePaymentAttempt.objects.blocking().filter(created_by=user).exists():
        raise CheckoutError('Resolve your current QRPh checkout before collecting Cash.', 409)
    member, pricing, name, remarks = checkout_snapshot(data)
    if member and OnlinePaymentAttempt.objects.blocking().filter(member=member).exists():
        raise CheckoutError('This member has an unresolved QRPh payment. Resolve it before collecting Cash.', 409)
    end_date = fulfill_member(member, pricing.duration_days, pricing.price)
    payment = Payment.objects.create(member=member, stored_member_id=member.member_id if member else 'GYMMSGUEST',
                                    stored_member_name=name, amount=pricing.price, payment_method='Cash',
                                    status='Completed', processed_by=user, remarks=remarks,
                                    membership_plan=pricing, stored_plan_label=pricing.duration_label,
                                    stored_duration_days=pricing.duration_days)
    CashPaymentRequest.objects.create(request_key=key, created_by=user, fingerprint=fingerprint,
                                      payment=payment, new_end_date=end_date)
    return payment, end_date


def serialize_payment(payment):
    return {'id': str(payment.pk), 'payment_date': timezone.localtime(payment.payment_date).strftime('%b %d, %Y %H:%M'),
            'stored_member_id': payment.stored_member_id, 'stored_member_name': payment.stored_member_name,
            'stored_plan_label': payment.stored_plan_label, 'stored_duration_days': payment.stored_duration_days,
            'amount': str(payment.amount), 'payment_method': payment.payment_method,
            'reference_number': payment.reference_number or '—', 'status': payment.status,
            'processed_by': payment.processor_display}
