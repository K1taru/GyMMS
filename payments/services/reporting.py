"""Shared audit filters and owner-only processor sales summaries."""
from datetime import datetime, timedelta

from django.db.models import Avg, Count, F, OuterRef, Q, Subquery, Sum
from django.utils import timezone

from payments.models import Payment
from .fulfillment import CheckoutError


PERIODS = {'1d': 1, '1w': 7, '1m': 30, '6m': 180, '1y': 365, 'all': None}


def can_audit_processors(user):
    return user.is_active and (user.is_superuser or getattr(user, 'role', '') == 'Owner')


def filtered_transactions(request, period=None):
    params = request.GET
    query = Payment.objects.select_related('member', 'processed_by').all()
    processor = params.get('processor', '').strip()
    # Reject the parameter itself, including an empty value, for unauthorized callers.
    if 'processor' in params and not can_audit_processors(request.user):
        raise CheckoutError('Owner access required for processor filters.', 403)
    if processor == 'unknown':
        query = query.filter(stored_processor_id__isnull=True)
    elif processor:
        if len(processor) > 19 or not processor.isascii() or not processor.isdecimal() or not 0 < int(processor) <= 9223372036854775807:
            raise CheckoutError('Invalid processor.', 400)
        query = query.filter(stored_processor_id=int(processor))

    search = params.get('search', '').strip()
    if search:
        query = query.filter(Q(stored_member_id__icontains=search) | Q(stored_member_name__icontains=search) |
                             Q(reference_number__icontains=search) | Q(id__icontains=search))
    dates = {}
    for key in ('date_from', 'date_to'):
        try:
            dates[key] = datetime.strptime(params.get(key, '').strip(), '%Y-%m-%d').date()
        except ValueError:
            pass
    if dates:
        if 'date_from' in dates:
            query = query.filter(payment_date__date__gte=dates['date_from'])
        if 'date_to' in dates:
            query = query.filter(payment_date__date__lte=dates['date_to'])
    elif period and PERIODS[period] is not None:
        query = query.filter(payment_date__gte=timezone.now() - timedelta(days=PERIODS[period]))

    method = params.get('payment_method', '').strip()
    if method == 'Digital':
        query = query.filter(payment_method__in=Payment.DIGITAL_PAYMENT_METHODS)
    elif method:
        query = query.filter(payment_method=method)
    member_type = params.get('member_type', '').strip()
    if member_type == 'member':
        query = query.exclude(stored_member_id='GYMMSGUEST')
    elif member_type == 'walkin':
        query = query.filter(stored_member_id='GYMMSGUEST')
    return query


def summary(query):
    totals = query.filter(status='Completed').aggregate(total_revenue=Sum('amount'),
        total_count=Count('id'), average_amount=Avg('amount'))
    return {key: float(value or 0) if key != 'total_count' else value for key, value in totals.items()}


def processor_rows(query, sales=False):
    if sales:
        query = query.filter(status='Completed')
    latest = query.filter(stored_processor_id=OuterRef('stored_processor_id')).order_by(
        '-payment_date', '-created_at', '-id')
    rows = query.order_by().values('stored_processor_id').annotate(
        username=Subquery(latest.values('stored_processor_username')[:1]),
        name=Subquery(latest.values('stored_processor_name')[:1]))
    if sales:
        rows = rows.annotate(total_revenue=Sum('amount'), total_count=Count('id'), average_amount=Avg('amount'))
        rows = rows.order_by('-total_revenue', F('stored_processor_id').asc(nulls_last=True))
    else:
        rows = rows.distinct().order_by(F('stored_processor_id').asc(nulls_last=True))
    result = []
    for row in rows:
        identity = Payment(stored_processor_id=row['stored_processor_id'],
                           stored_processor_username=row['username'] or '', stored_processor_name=row['name'] or '')
        item = {'processor': str(row['stored_processor_id']) if row['stored_processor_id'] is not None else 'unknown',
                'label': identity.processor_display}
        if sales:
            item.update(total_revenue=float(row['total_revenue']), total_count=row['total_count'],
                        average_amount=float(row['average_amount']))
        result.append(item)
    return result


def owner_report(request, query):
    if not can_audit_processors(request.user):
        return {}
    return {'processor_options': processor_rows(Payment.objects.all()), 'processor_sales': processor_rows(query, sales=True)}
