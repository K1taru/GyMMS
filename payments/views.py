from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from memberships.models import Member
from .models import Payment, MembershipPricing


@login_required
def payments(request):
    """
    Main payment processing page
    """
    # Get member_id from URL parameter if provided (from bridge)
    member_id = request.GET.get('member_id')
    is_walkin = request.GET.get('walkin') == 'true'
    selected_member = None
    today = timezone.localdate()
    
    if member_id:
        try:
            selected_member = Member.objects.get(member_id=member_id, is_deleted=False)
        except Member.DoesNotExist:
            messages.error(request, f'Member {member_id} not found.')
    
    # Get all active pricing options
    pricing_options = MembershipPricing.objects.filter(is_active=True)
    
    # Get recent payments (last 5)
    recent_payments = Payment.objects.select_related('member', 'processed_by')[:5]
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        recent_payments = recent_payments.filter(
            Q(stored_member_id__icontains=search_query) |
            Q(stored_member_name__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )
    
    context = {
        'selected_member': selected_member,
        'pricing_options': pricing_options,
        'recent_payments': recent_payments,
        'search_query': search_query,
        'today': today,
        'is_walkin': is_walkin,
    }
    
    return render(request, "payments/payments.html", context)


def staff_endpoint(view):
    from functools import wraps
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required.'}, status=401)
        if not request.user.is_active or (getattr(request.user, 'role', '') not in ('Owner', 'Staff') and not request.user.is_superuser):
            return JsonResponse({'success': False, 'message': 'Staff access required.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapped


def request_data(request):
    import json
    from .services.fulfillment import CheckoutError
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except (ValueError, UnicodeDecodeError):
            raise CheckoutError('Invalid request body.')
    return request.POST


@staff_endpoint
@sensitive_post_parameters('cash_password')
@sensitive_variables('data', 'password')
def process_payment(request):
    from .services.fulfillment import process_cash, serialize_payment, CheckoutError
    from django.db import IntegrityError
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)
    try:
        data = request_data(request)
        if data.get('payment_method') == 'Cash':
            password = data.get('cash_password')
            if not isinstance(password, str) or not password:
                raise CheckoutError('Enter your password to authorize this cash payment.')
            if not request.user.check_password(password):
                raise CheckoutError('Incorrect password. Enter the password for your signed-in account.', 403)
        payment, end_date = process_cash(request.user, data)
        is_walkin = payment.stored_member_id == 'GYMMSGUEST'
        message = 'Cash payment processed successfully.'
        return JsonResponse({'success': True, 'message': message, 'payment_id': str(payment.pk),
                             'new_end_date': end_date.isoformat() if end_date else None,
                             'is_walkin': is_walkin, 'payment': serialize_payment(payment)})
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=exc.status)
    except IntegrityError:
        return JsonResponse({'success': False, 'message': 'Payment request conflict. Retry with the same request key.'}, status=409)


@staff_endpoint
def qrph_create(request):
    from .services.qrph import create_attempt, serialize_attempt
    from .services.fulfillment import CheckoutError
    from django.db import IntegrityError
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)
    try:
        attempt = create_attempt(request.user, request_data(request))
        return JsonResponse({'success': True, 'attempt': serialize_attempt(attempt)}, status=202)
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=exc.status)
    except IntegrityError:
        return JsonResponse({'success': False, 'message': 'Another checkout is unresolved. Resume your current payment.'}, status=409)


@staff_endpoint
def qrph_current(request):
    from .models import OnlinePaymentAttempt
    from .services.qrph import serialize_attempt
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET required.'}, status=405)
    attempt = OnlinePaymentAttempt.objects.blocking().filter(created_by=request.user).select_related('payment__processed_by').first()
    return JsonResponse({'success': True, 'attempt': serialize_attempt(attempt) if attempt else None})


def accessible_attempt(request, attempt_id):
    from .models import OnlinePaymentAttempt
    query = OnlinePaymentAttempt.objects.select_related('payment__processed_by')
    if getattr(request.user, 'role', '') != 'Owner' and not request.user.is_superuser:
        query = query.filter(created_by=request.user)
    return query.filter(pk=attempt_id).first()


@staff_endpoint
def qrph_detail(request, attempt_id):
    from .services.qrph import serialize_attempt
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET required.'}, status=405)
    attempt = accessible_attempt(request, attempt_id)
    if not attempt:
        return JsonResponse({'success': False, 'message': 'Payment attempt not found.'}, status=404)
    return JsonResponse({'success': True, 'attempt': serialize_attempt(attempt)})


@staff_endpoint
def qrph_cancel(request, attempt_id):
    from .services.qrph import request_cancel, serialize_attempt
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)
    attempt = accessible_attempt(request, attempt_id)
    if not attempt:
        return JsonResponse({'success': False, 'message': 'Payment attempt not found.'}, status=404)
    attempt = request_cancel(attempt.pk)
    return JsonResponse({'success': True, 'attempt': serialize_attempt(attempt)})


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def paymongo_webhook(request, mode):
    from .services.qrph import receive_webhook
    from .services.fulfillment import CheckoutError
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)
    if len(request.body) > 1024 * 1024:
        return JsonResponse({'success': False, 'message': 'Payload too large.'}, status=413)
    try:
        receive_webhook(mode, request.body, request.headers.get('Paymongo-Signature', ''))
        return JsonResponse({'success': True})
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=exc.status)


@login_required
def search_members(request):
    """
    Search for members (AJAX endpoint)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'members': []})
    
    members = Member.objects.filter(
        Q(member_id__icontains=query) |
        Q(name__icontains=query) |
        Q(phone_number__icontains=query) |
        Q(email__icontains=query),
        is_deleted=False
    )[:10]  # Limit to 10 results
    
    today = timezone.localdate()
    
    members_data = []
    for m in members:
        # Determine status
        if m.is_active:
            if m.end_date >= today:
                if m.is_expiring_soon():
                    status = 'expiring'
                    is_expiring_soon = True
                else:
                    status = 'active'
                    is_expiring_soon = False
            else:
                status = 'expired'
                is_expiring_soon = False
        else:
            status = 'inactive'
            is_expiring_soon = False
        
        members_data.append({
            'member_id': m.member_id,
            'name': m.name,
            'phone_number': m.phone_number,
            'email': m.email or '',
            'status': status,
            'is_expiring_soon': is_expiring_soon,
            'end_date': m.end_date.strftime('%b %d, %Y'),
            'photo': m.photo.url if m.photo else None
        })
    
    return JsonResponse({'members': members_data})


def history_data(request, period=None):
    from .services.reporting import filtered_transactions, summary, owner_report
    from .services.fulfillment import serialize_payment
    query = filtered_transactions(request)
    try:
        per_page = int(request.GET.get('per_page', '10'))
    except ValueError:
        per_page = 10
    if per_page not in (10, 25, 50, 100):
        per_page = 10
    page = Paginator(query, per_page).get_page(request.GET.get('page', '1'))
    summary_query = filtered_transactions(request, period=period) if period else query
    data = {
        'transactions': [serialize_payment(payment) for payment in page],
        'pagination': {
            'current_page': page.number, 'total_pages': page.paginator.num_pages,
            'has_previous': page.has_previous(), 'has_next': page.has_next(),
            'start_index': page.start_index(), 'end_index': page.end_index(),
            'total_count': page.paginator.count, 'per_page': per_page,
        },
        'stats': summary(summary_query),
        **owner_report(request, summary_query),
    }
    return page, data


@login_required
def transaction_history(request):
    from .services.fulfillment import CheckoutError
    from .services.reporting import can_audit_processors, PERIODS
    try:
        period = request.GET.get('period', '1d')
        if period not in PERIODS:
            period = '1d'
        page, data = history_data(request, period=period)
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=exc.status)
    context = {key: request.GET.get(key, '').strip() for key in
               ('search', 'date_from', 'date_to', 'payment_method', 'member_type', 'processor')}
    context['search_query'] = context.pop('search')
    context.update(data['pagination'])
    context.update(data['stats'])
    context.update({key: data[key] for key in ('processor_options', 'processor_sales') if key in data})
    context.update(pagination_count=page.paginator.count, transactions=page, can_audit_processors=can_audit_processors(request.user), period=period)
    return render(request, 'payments/transaction_history.html', context)


@login_required
def transaction_stats(request):
    from .services.fulfillment import CheckoutError
    from .services.reporting import filtered_transactions, summary, owner_report, PERIODS
    period = request.GET.get('period', '1d').lower()
    if period not in PERIODS:
        period = '1d'
    try:
        query = filtered_transactions(request, period=period)
        return JsonResponse({**summary(query), 'period': period, **owner_report(request, query)})
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=exc.status)


@login_required
def get_transactions_ajax(request):
    from .services.fulfillment import CheckoutError
    try:
        from .services.reporting import PERIODS
        period = request.GET.get('period', 'all')
        if period not in PERIODS:
            period = 'all'
        _, data = history_data(request, period=period)
        return JsonResponse(data)
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=exc.status)
