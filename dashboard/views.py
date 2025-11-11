from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta

from .models import GymCheckIn, DashboardStats
from memberships.models import Member
from payments.models import Payment

@login_required
def dashboard(request):
    today = timezone.now().date()
    now = timezone.now()
    
    # Get today's check-ins
    today_check_ins = GymCheckIn.objects.filter(date=today)
    
    # Daily walk-ins (members who checked in today)
    daily_walk_ins = today_check_ins.values('member').distinct().count()
    
    # Total check-ins today
    total_check_ins_today = today_check_ins.count()
    
    # Active members currently in gym (checked in but not checked out)
    active_in_gym = today_check_ins.filter(check_out_time__isnull=True).count()
    
    # Monthly statistics
    month_start = today.replace(day=1)
    monthly_check_ins = GymCheckIn.objects.filter(
        date__gte=month_start,
        date__lte=today
    ).values('member').distinct().count()
    
    # Total active members
    total_active_members = Member.objects.filter(is_active=True).count()
    
    # New members this month
    new_members_this_month = Member.objects.filter(
        date_created__gte=month_start,
        date_created__lte=now
    ).count()
    
    # Revenue statistics
    today_revenue = Payment.objects.filter(
        payment_date__date=today,
        status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_revenue = Payment.objects.filter(
        payment_date__gte=month_start,
        payment_date__lte=now,
        status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent check-ins (last 10)
    recent_check_ins = today_check_ins.select_related('member')[:10]
    
    # Membership expiring soon (within 3 days)
    expiring_soon = Member.objects.filter(
        is_active=True,
        end_date__gte=today,
        end_date__lte=today + timedelta(days=3)
    ).count()
    
    # Peak hours data (check-ins by hour today)
    peak_hours = today_check_ins.extra(
        select={'hour': 'EXTRACT(hour FROM check_in_time)'}
    ).values('hour').annotate(count=Count('id')).order_by('hour')
    
    # Calculate percentages for chart visualization
    max_count = max([h['count'] for h in peak_hours], default=1)
    peak_hours_data = []
    for h in peak_hours:
        peak_hours_data.append({
            'hour': int(h['hour']),
            'count': h['count'],
            'percentage': (h['count'] / max_count * 100) if max_count > 0 else 10
        })
    
    context = {
        'daily_walk_ins': daily_walk_ins,
        'monthly_check_ins': monthly_check_ins,
        'active_in_gym': active_in_gym,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'active_members': total_active_members,
        'expiring_soon': expiring_soon,
        'new_members': new_members_this_month,
        'recent_check_ins': recent_check_ins,
        'peak_hours': peak_hours_data,
        'current_time': now,
    }
    
    return render(request, "dashboard/dashboard.html", context)
