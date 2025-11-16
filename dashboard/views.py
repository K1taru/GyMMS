from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta, datetime
import json
import zoneinfo

from .models import GymCheckIn, DashboardStats
from memberships.models import Member
from payments.models import Payment

@login_required
def dashboard(request):
    # Get current time in Manila timezone
    manila_tz = zoneinfo.ZoneInfo('Asia/Manila')
    now = timezone.now()
    manila_now = now.astimezone(manila_tz)
    today = manila_now.date()
    
    # Get today's check-ins
    today_check_ins = GymCheckIn.objects.filter(date=today)
    
    # Calculate start and end of today in Manila timezone
    manila_today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=manila_tz)
    manila_today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=manila_tz)
    
    # Daily walk-ins (guest payments only - GYMMSGUEST)
    daily_walk_ins = Payment.objects.filter(
        payment_date__gte=manila_today_start,
        payment_date__lte=manila_today_end,
        stored_member_id='GYMMSGUEST',
        status='Completed'
    ).count()
    
    # Member check-ins (unique registered members who checked in today)
    member_check_ins = today_check_ins.values('member').distinct().count()
    
    # Active members currently in gym (checked in but not checked out)
    active_in_gym = today_check_ins.filter(check_out_time__isnull=True).count()
    
    # Monthly statistics
    month_start = today.replace(day=1)
    
    # Total active members
    total_active_members = Member.objects.filter(is_active=True, is_deleted=False).count()
    
    # New members this month (exclude deleted members)
    new_members_this_month = Member.objects.filter(
        date_created__gte=month_start,
        date_created__lte=now,
        is_deleted=False
    ).count()
    
    # Revenue statistics
    # Debug: Print today's date for verification
    print(f"[DASHBOARD REVENUE] Today's date (Manila): {today}")
    print(f"[DASHBOARD REVENUE] Manila now: {manila_now}")
    print(f"[DASHBOARD REVENUE] UTC now: {now}")
    
    # Calculate start and end of today in Manila timezone
    manila_today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=manila_tz)
    manila_today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=manila_tz)
    
    print(f"[DASHBOARD REVENUE] Today start (Manila): {manila_today_start}")
    print(f"[DASHBOARD REVENUE] Today end (Manila): {manila_today_end}")
    
    # Get today's payments with detailed logging
    today_payments = Payment.objects.filter(
        payment_date__gte=manila_today_start,
        payment_date__lte=manila_today_end,
        status='Completed'
    )
    print(f"[DASHBOARD REVENUE] Today's payment count: {today_payments.count()}")
    for payment in today_payments:
        print(f"[DASHBOARD REVENUE] Payment: {payment.id} - Amount: {payment.amount} - Date: {payment.payment_date} - Status: {payment.status}")
    
    today_revenue = today_payments.aggregate(total=Sum('amount'))['total'] or 0
    print(f"[DASHBOARD REVENUE] Today's total revenue: {today_revenue}")
    
    # Calculate start of month in Manila timezone
    month_start_dt = datetime.combine(month_start, datetime.min.time()).replace(tzinfo=manila_tz)
    
    # Get monthly payments
    monthly_payments = Payment.objects.filter(
        payment_date__gte=month_start_dt,
        payment_date__lte=manila_now,
        status='Completed'
    )
    print(f"[DASHBOARD REVENUE] Monthly payment count: {monthly_payments.count()}")
    
    monthly_revenue = monthly_payments.aggregate(total=Sum('amount'))['total'] or 0
    print(f"[DASHBOARD REVENUE] Monthly total revenue: {monthly_revenue}")
    
    # Recent check-ins - combine member check-ins and walk-in payments
    # Get member check-ins (ALL, no limit)
    member_checkins = list(today_check_ins.select_related('member').order_by('-check_in_time'))
    
    # Get walk-in payments from today (ALL, no limit)
    walkin_payments = Payment.objects.filter(
        payment_date__gte=manila_today_start,
        payment_date__lte=manila_today_end,
        stored_member_id='GYMMSGUEST',
        status='Completed'
    ).order_by('-payment_date')
    
    # Combine both into a unified list with consistent structure
    combined_checkins = []
    
    # Add member check-ins
    for checkin in member_checkins:
        photo_url = checkin.member.photo.url if checkin.member.photo else None
        combined_checkins.append({
            'type': 'member',
            'name': checkin.member.name,
            'photo': photo_url,
            'time': checkin.check_in_time,
            'check_out_time': checkin.check_out_time,
            'duration': None  # We'll calculate this in template
        })
    
    # Add walk-in payments
    for payment in walkin_payments:
        combined_checkins.append({
            'type': 'walkin',
            'name': payment.stored_member_name,
            'photo': None,  # Walk-ins don't have photos
            'time': payment.payment_date,
            'check_out_time': None,
            'duration': None
        })
    
    # Sort by time (most recent first) - NO LIMIT
    combined_checkins.sort(key=lambda x: x['time'], reverse=True)
    recent_check_ins = combined_checkins
    
    # Membership expiring soon (within 3 days, exclude deleted members)
    expiring_soon = Member.objects.filter(
        is_active=True,
        is_deleted=False,
        end_date__gte=today,
        end_date__lte=today + timedelta(days=3)
    ).count()
    
    # Peak hours data (check-ins by hour today) - Use Manila timezone for hour extraction
    # Include both member check-ins and walk-in payments
    peak_hours_raw = today_check_ins.select_related('member')
    
    # Get walk-in payments from today
    walkin_payments_for_peak = Payment.objects.filter(
        payment_date__gte=manila_today_start,
        payment_date__lte=manila_today_end,
        stored_member_id='GYMMSGUEST',
        status='Completed'
    )
    
    # Convert to Manila timezone and group by hour
    from collections import defaultdict
    hour_counts = defaultdict(int)
    
    # Add member check-ins
    for checkin in peak_hours_raw:
        # Convert check_in_time to Manila timezone
        manila_checkin_time = checkin.check_in_time.astimezone(manila_tz)
        hour = manila_checkin_time.hour
        hour_counts[hour] += 1
    
    # Add walk-in payments
    for payment in walkin_payments_for_peak:
        # Convert payment_date to Manila timezone
        manila_payment_time = payment.payment_date.astimezone(manila_tz)
        hour = manila_payment_time.hour
        hour_counts[hour] += 1
    
    # Convert to list format
    peak_hours_data = []
    for hour, count in hour_counts.items():
        peak_hours_data.append({
            'hour': hour,
            'count': count
        })
    
    # Sort by hour
    peak_hours_data.sort(key=lambda x: x['hour'])
    
    context = {
        'daily_walk_ins': daily_walk_ins,
        'member_check_ins': member_check_ins,
        'active_in_gym': active_in_gym,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'active_members': total_active_members,
        'expiring_soon': expiring_soon,
        'new_members': new_members_this_month,
        'recent_check_ins': recent_check_ins,
        'peak_hours': json.dumps(peak_hours_data),  # JSON for JavaScript
        'current_time': now,
    }
    
    return render(request, "dashboard/dashboard.html", context)


@login_required
@require_http_methods(["GET"])
def search_active_members(request):
    """Search for active and expiring members for check-in"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'members': []})
    
    today = timezone.now().date()
    expiring_threshold = today + timedelta(days=7)
    
    # Search members (active, expiring, and inactive)
    members = Member.objects.filter(
        is_deleted=False
    ).filter(
        Q(member_id__icontains=query) |
        Q(name__icontains=query)
    )[:10]
    
    results = []
    for member in members:
        # Determine status based on end_date and is_active flag
        if member.end_date < today:
            status = 'expired'
        elif not member.is_active:
            status = 'inactive'
        elif member.end_date <= expiring_threshold:
            status = 'expiring'
        else:
            status = 'active'
        
        results.append({
            'member_id': member.member_id,
            'name': member.name,
            'status': status,
            'end_date': member.end_date.strftime('%Y-%m-%d'),
            'photo': member.photo.url if member.photo else None
        })
    
    return JsonResponse({'members': results})


@login_required
@require_http_methods(["POST"])
def log_checkin(request):
    """Log a member check-in"""
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        
        print(f"[CHECK-IN] Received request for member_id: {member_id}")
        
        if not member_id:
            print("[CHECK-IN] Error: No member_id provided")
            return JsonResponse({'success': False, 'error': 'Member ID is required'})
        
        # Get member
        try:
            member = Member.objects.get(member_id=member_id, is_deleted=False)
            print(f"[CHECK-IN] Found member: {member.name} ({member.member_id})")
        except Member.DoesNotExist:
            print(f"[CHECK-IN] Error: Member {member_id} not found")
            return JsonResponse({'success': False, 'error': 'Member not found'})
        
        # Check if member is active or expiring soon
        today = timezone.now().date()
        if member.end_date < today:
            print(f"[CHECK-IN] Error: Member {member_id} has expired")
            return JsonResponse({'success': False, 'error': 'Member membership has expired. Please renew membership first.'})
        
        if not member.is_active:
            print(f"[CHECK-IN] Error: Member {member_id} is inactive")
            return JsonResponse({'success': False, 'error': 'Member account is inactive. Please process payment first.'})
        
        # Get Manila timezone for accurate time comparison
        manila_tz = zoneinfo.ZoneInfo('Asia/Manila')
        now = timezone.now()
        manila_now = now.astimezone(manila_tz)
        
        # Check how many times member has checked in today (max 3)
        today_checkins = GymCheckIn.objects.filter(
            member=member,
            date=today
        ).order_by('-check_in_time')
        
        today_checkins_count = today_checkins.count()
        
        if today_checkins_count >= 3:
            print(f"[CHECK-IN] Error: Member {member_id} has reached maximum check-ins (3) for today")
            return JsonResponse({'success': False, 'error': 'Maximum check-ins (3) reached for today.'})
        
        # Check if member has checked in recently (within last hour)
        if today_checkins_count > 0:
            last_checkin = today_checkins.first()
            last_checkin_time = last_checkin.check_in_time.astimezone(manila_tz)
            time_diff = manila_now - last_checkin_time
            time_diff_minutes = int(time_diff.total_seconds() / 60)
            
            if time_diff_minutes < 60:
                # Calculate remaining time
                remaining_minutes = 60 - time_diff_minutes
                hours = remaining_minutes // 60
                minutes = remaining_minutes % 60
                
                if hours > 0:
                    time_left = f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    time_left = f"{minutes} minute{'s' if minutes != 1 else ''}"
                
                print(f"[CHECK-IN] Error: Member {member_id} checked in {time_diff_minutes} minutes ago. Must wait {remaining_minutes} more minutes.")
                return JsonResponse({
                    'success': False, 
                    'error': f'Please wait {time_left} before checking in again.',
                    'time_left_minutes': remaining_minutes
                })
        
        # Create check-in record (member can check in up to 3 times)
        checkin = GymCheckIn.objects.create(member=member)
        print(f"[CHECK-IN] Success: Created check-in record ID {checkin.id} for {member.name} at {checkin.check_in_time}")
        
        return JsonResponse({'success': True, 'checkin_id': checkin.id})
        
    except Exception as e:
        print(f"[CHECK-IN] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def get_stats(request):
    """Get updated dashboard statistics for AJAX refresh"""
    # Get current time in Manila timezone
    manila_tz = zoneinfo.ZoneInfo('Asia/Manila')
    now = timezone.now()
    manila_now = now.astimezone(manila_tz)
    today = manila_now.date()
    
    # Get today's check-ins
    today_check_ins = GymCheckIn.objects.filter(date=today)
    
    # Calculate today's date range in Manila timezone
    manila_today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=manila_tz)
    manila_today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=manila_tz)
    
    # Daily walk-ins (guest payments only - GYMMSGUEST)
    daily_walk_ins = Payment.objects.filter(
        payment_date__gte=manila_today_start,
        payment_date__lte=manila_today_end,
        stored_member_id='GYMMSGUEST',
        status='Completed'
    ).count()
    
    # Member check-ins (registered members who checked in today)
    member_check_ins = today_check_ins.count()
    
    # Recent check-ins - combine member check-ins and walk-in payments
    # Get member check-ins (ALL, no limit)
    member_checkins = list(today_check_ins.select_related('member').order_by('-check_in_time'))
    
    # Get walk-in payments from today (ALL, no limit)
    walkin_payments = Payment.objects.filter(
        payment_date__gte=manila_today_start,
        payment_date__lte=manila_today_end,
        stored_member_id='GYMMSGUEST',
        status='Completed'
    ).order_by('-payment_date')
    
    # Combine both into a unified list
    combined_checkins = []
    
    # Add member check-ins
    for ci in member_checkins:
        photo_url = ci.member.photo.url if ci.member.photo else None
        combined_checkins.append({
            'type': 'member',
            'name': ci.member.name,
            'photo': photo_url,
            'time': ci.check_in_time,
            'check_out_time': ci.check_out_time
        })
    
    # Add walk-in payments
    for payment in walkin_payments:
        combined_checkins.append({
            'type': 'walkin',
            'name': payment.stored_member_name,
            'photo': None,
            'time': payment.payment_date,
            'check_out_time': None
        })
    
    # Sort by time (most recent first) - NO LIMIT
    combined_checkins.sort(key=lambda x: x['time'], reverse=True)
    recent_check_ins = combined_checkins
    
    # Format recent check-ins
    recent_list = []
    for item in recent_check_ins:
        # Calculate time ago
        time_diff = timezone.now() - item['time']
        if time_diff.seconds < 60:
            time_ago = "Just now"
        elif time_diff.seconds < 3600:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        recent_list.append({
            'type': item['type'],
            'member_name': item['name'],
            'photo': item['photo'],
            'time_ago': time_ago,
        })
    
    return JsonResponse({
        'success': True,
        'daily_walk_ins': daily_walk_ins,
        'member_check_ins': member_check_ins,
        'recent_check_ins': recent_list
    })


@login_required
def debug_checkins(request):
    """Debug endpoint to check check-in data"""
    today = timezone.now().date()
    
    # Get all check-ins
    all_checkins = GymCheckIn.objects.all()
    today_checkins = GymCheckIn.objects.filter(date=today)
    
    # Get raw SQL data
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM dashboard_gymcheckin")
        raw_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT id, member_id, check_in_time, date 
            FROM dashboard_gymcheckin 
            ORDER BY check_in_time DESC 
            LIMIT 10
        """)
        raw_records = cursor.fetchall()
    
    debug_data = {
        'total_checkins': all_checkins.count(),
        'today_checkins': today_checkins.count(),
        'raw_count': raw_count,
        'today_date': str(today),
        'recent_checkins': [
            {
                'id': ci.id,
                'member': ci.member.name,
                'member_id': ci.member.member_id,
                'time': ci.check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
                'date': str(ci.date)
            }
            for ci in today_checkins[:10]
        ],
        'raw_records': [
            {
                'id': r[0],
                'member_id': r[1],
                'time': str(r[2]),
                'date': str(r[3])
            }
            for r in raw_records
        ]
    }
    
    return JsonResponse(debug_data)
