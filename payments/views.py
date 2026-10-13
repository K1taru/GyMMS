from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Avg, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta, datetime
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
def process_payment(request):
    from .services.fulfillment import process_cash, serialize_payment, CheckoutError
    from django.db import IntegrityError
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)
    try:
        payment, end_date = process_cash(request.user, request_data(request))
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
    from .models import OnlinePaymentAttempt, UNRESOLVED_STATUSES
    from .services.qrph import serialize_attempt
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET required.'}, status=405)
    attempt = OnlinePaymentAttempt.objects.filter(created_by=request.user, status__in=UNRESOLVED_STATUSES).select_related('payment__processed_by').first()
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
    return JsonResponse({'success': True, 'attempt': serialize_attempt(request_cancel(attempt.pk))})


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


@login_required
def transaction_history(request):
    """
    Transaction history page with pagination and filters
    """
    # Start with all payments
    transactions = Payment.objects.select_related('member', 'processed_by').all()
    
    # Apply filters
    search_query = request.GET.get('search', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(stored_member_id__icontains=search_query) |
            Q(stored_member_name__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Date filters
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(payment_date__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(payment_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Payment method filter
    payment_method = request.GET.get('payment_method', '').strip()
    if payment_method:
        if payment_method == 'Digital':
            # Filter for all digital payment methods (exclude Cash)
            digital_methods = ['QRPh', 'GCash', 'Maya', 'GoTyme', 'Bank Transfer', 'PayPal', 'Debit Card', 'Credit Card']
            transactions = transactions.filter(payment_method__in=digital_methods)
        else:
            transactions = transactions.filter(payment_method=payment_method)
    
    # Member type filter (members vs walk-ins)
    member_type = request.GET.get('member_type', '').strip()
    if member_type:
        if member_type == 'member':
            # Regular members (not walk-ins)
            transactions = transactions.exclude(stored_member_id='GYMMSGUEST')
        elif member_type == 'walkin':
            # Walk-in guests only
            transactions = transactions.filter(stored_member_id='GYMMSGUEST')
    
    # Calculate summary statistics for filtered results
    stats = transactions.filter(status='Completed').aggregate(
        total_revenue=Sum('amount'),
        total_count=Count('id'),
        average_amount=Avg('amount')
    )
    
    # Pagination
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    page = request.GET.get('page', '1')
    
    paginator = Paginator(transactions, per_page)
    
    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    # Calculate start and end index
    start_index = (transactions_page.number - 1) * per_page + 1
    end_index = min(start_index + per_page - 1, paginator.count)
    
    context = {
        'transactions': transactions_page,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'payment_method': payment_method,
        'member_type': member_type,
        'total_revenue': stats['total_revenue'] or 0,
        'total_count': stats['total_count'] or 0,
        'average_amount': stats['average_amount'] or 0,
        'current_page': transactions_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': transactions_page.has_previous(),
        'has_next': transactions_page.has_next(),
        'start_index': start_index,
        'end_index': end_index,
        'per_page': per_page,
    }
    
    return render(request, "payments/transaction_history.html", context)


@login_required
def transaction_stats(request):
    """
    Get transaction statistics for a specific time period (AJAX endpoint)
    Also respects search and filter parameters
    """
    period = request.GET.get('period', '1d').lower()
    
    # Calculate date range based on period
    now = timezone.now()
    
    period_map = {
        '1d': timedelta(days=1),
        '1w': timedelta(weeks=1),
        '1m': timedelta(days=30),
        '6m': timedelta(days=180),
        '1y': timedelta(days=365),
        'all': None  # All time
    }
    
    delta = period_map.get(period)
    
    # Start with all transactions
    transactions = Payment.objects.filter(status='Completed')
    
    # Apply time period filter
    if delta:
        start_date = now - delta
        transactions = transactions.filter(payment_date__gte=start_date)
    
    # Apply additional filters (search, payment method, member type, date range)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(stored_member_id__icontains=search_query) |
            Q(stored_member_name__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Date filters (override time period if provided)
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            # If date_from is provided, use it instead of period-based start_date
            transactions = Payment.objects.filter(status='Completed', payment_date__date__gte=date_from_obj)
            if search_query:
                transactions = transactions.filter(
                    Q(stored_member_id__icontains=search_query) |
                    Q(stored_member_name__icontains=search_query) |
                    Q(reference_number__icontains=search_query) |
                    Q(id__icontains=search_query)
                )
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(payment_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Payment method filter
    payment_method = request.GET.get('payment_method', '').strip()
    if payment_method:
        if payment_method == 'Digital':
            digital_methods = ['QRPh', 'GCash', 'Maya', 'GoTyme', 'Bank Transfer', 'PayPal', 'Debit Card', 'Credit Card']
            transactions = transactions.filter(payment_method__in=digital_methods)
        else:
            transactions = transactions.filter(payment_method=payment_method)
    
    # Member type filter (members vs walk-ins)
    member_type = request.GET.get('member_type', '').strip()
    if member_type:
        if member_type == 'member':
            transactions = transactions.exclude(stored_member_id='GYMMSGUEST')
        elif member_type == 'walkin':
            transactions = transactions.filter(stored_member_id='GYMMSGUEST')
    
    # Calculate statistics
    stats = transactions.filter(status='Completed').aggregate(
        total_revenue=Sum('amount'),
        total_count=Count('id'),
        average_amount=Avg('amount')
    )
    
    return JsonResponse({
        'total_revenue': float(stats['total_revenue'] or 0),
        'total_count': stats['total_count'] or 0,
        'average_amount': float(stats['average_amount'] or 0),
        'period': period
    })


@login_required
def get_transactions_ajax(request):
    """
    AJAX endpoint for fetching filtered transactions without page reload
    """
    # Start with all payments
    transactions = Payment.objects.select_related('member', 'processed_by').all()
    
    # Apply filters
    search_query = request.GET.get('search', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(stored_member_id__icontains=search_query) |
            Q(stored_member_name__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Date filters
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(payment_date__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(payment_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Payment method filter
    payment_method = request.GET.get('payment_method', '').strip()
    if payment_method:
        if payment_method == 'Digital':
            # Filter for all digital payment methods (exclude Cash)
            digital_methods = ['QRPh', 'GCash', 'Maya', 'GoTyme', 'Bank Transfer', 'PayPal', 'Debit Card', 'Credit Card']
            transactions = transactions.filter(payment_method__in=digital_methods)
        else:
            transactions = transactions.filter(payment_method=payment_method)
    
    # Member type filter (members vs walk-ins)
    member_type = request.GET.get('member_type', '').strip()
    if member_type:
        if member_type == 'member':
            # Regular members (not walk-ins)
            transactions = transactions.exclude(stored_member_id='GYMMSGUEST')
        elif member_type == 'walkin':
            # Walk-in guests only
            transactions = transactions.filter(stored_member_id='GYMMSGUEST')
    
    # Calculate summary statistics for filtered results
    stats = transactions.filter(status='Completed').aggregate(
        total_revenue=Sum('amount'),
        total_count=Count('id'),
        average_amount=Avg('amount')
    )
    
    # Pagination
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    page = request.GET.get('page', '1')
    
    paginator = Paginator(transactions, per_page)
    
    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    # Calculate start and end index
    start_index = (transactions_page.number - 1) * per_page + 1
    end_index = min(start_index + per_page - 1, paginator.count)
    
    # Prepare transaction data for JSON response
    transactions_data = []
    for transaction in transactions_page:
        transactions_data.append({
            'id': str(transaction.id),
            'payment_date': transaction.payment_date.strftime('%b %d, %Y %H:%M'),
            'stored_member_id': transaction.stored_member_id,
            'stored_member_name': transaction.stored_member_name,
            'stored_plan_label': transaction.stored_plan_label or 'N/A',
            'stored_duration_days': transaction.stored_duration_days,
            'amount': str(transaction.amount),
            'payment_method': transaction.payment_method,
            'reference_number': transaction.reference_number or '—',
            'processed_by': transaction.processed_by.username if transaction.processed_by else '—',
        })
    
    return JsonResponse({
        'transactions': transactions_data,
        'pagination': {
            'current_page': transactions_page.number,
            'total_pages': paginator.num_pages,
            'has_previous': transactions_page.has_previous(),
            'has_next': transactions_page.has_next(),
            'start_index': start_index,
            'end_index': end_index,
            'total_count': paginator.count,
            'per_page': per_page,
        },
        'stats': {
            'total_revenue': float(stats['total_revenue'] or 0),
            'total_count': stats['total_count'] or 0,
            'average_amount': float(stats['average_amount'] or 0),
        }
    })
