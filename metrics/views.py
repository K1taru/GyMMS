from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dashboard.models import GymCheckIn, DashboardStats
from payments.models import Payment
from memberships.models import Member
from metrics.models import ActiveMemberSnapshot
import calendar
import statistics


def calculate_dynamic_scale(data):
    """
    Calculate suggested Y-axis min and max for better visualization
    Uses statistical methods to avoid charts always hitting peak
    """
    if not data or all(v == 0 for v in data):
        return {'suggestedMin': 0, 'suggestedMax': 10}
    
    # Filter out zero values for statistical calculation
    non_zero_data = [v for v in data if v > 0]
    
    if not non_zero_data:
        return {'suggestedMin': 0, 'suggestedMax': 10}
    
    data_min = min(data)
    data_max = max(data)
    data_range = data_max - data_min
    
    # Calculate statistics
    mean = statistics.mean(non_zero_data)
    
    if len(non_zero_data) > 1:
        stdev = statistics.stdev(non_zero_data)
    else:
        stdev = 0
    
    # Use a padding strategy based on data characteristics
    if data_range == 0:
        # All values are the same
        padding = max(data_max * 0.2, 5)
        suggested_min = max(0, data_min - padding)
        suggested_max = data_max + padding
    else:
        # Add 15-25% padding above max value
        # Use larger padding for small datasets
        padding_percentage = 0.25 if len(data) < 10 else 0.15
        padding = data_range * padding_percentage
        
        # For datasets with high variance, add extra headroom
        if stdev > mean * 0.5:
            padding *= 1.5
        
        suggested_min = max(0, data_min - (padding * 0.3))
        suggested_max = data_max + padding
    
    # Round to nice numbers
    if suggested_max < 10:
        suggested_max = round(suggested_max + 0.5)
    elif suggested_max < 100:
        suggested_max = (int(suggested_max / 5) + 1) * 5
    else:
        # Round to nearest 10, 50, or 100 depending on magnitude
        magnitude = 10 ** (len(str(int(suggested_max))) - 1)
        suggested_max = ((int(suggested_max / magnitude) + 1) * magnitude)
    
    return {
        'suggestedMin': round(suggested_min, 2),
        'suggestedMax': round(suggested_max, 2)
    }

@login_required
def metrics(request):
    return render(request, "metrics/metrics.html")

@login_required
def get_metrics_data(request):
    """API endpoint to fetch metrics data based on metric type and time period"""
    metric_type = request.GET.get('metric', 'check_ins')
    period = request.GET.get('period', '1m')
    
    # Calculate date range and labels based on period
    end_date = timezone.now().date()
    labels = []
    date_ranges = []
    
    if period == '1d':
        start_date = end_date
        # Hourly breakdown for 1 day
        for hour in range(0, 24, 4):
            labels.append(f'{hour}:00')
            date_ranges.append((hour, hour + 4))
            
    elif period == '1w':
        start_date = end_date - timedelta(days=6)
        # Daily breakdown for 1 week
        for i in range(7):
            date = start_date + timedelta(days=i)
            labels.append(date.strftime('%a %d'))  # e.g., "Mon 13"
            date_ranges.append(date)
            
    elif period == '1m':
        start_date = end_date - timedelta(days=29)
        # Daily breakdown for last 30 days (show every 5 days to avoid clutter)
        days_to_show = [0, 5, 10, 15, 20, 25, 29]
        for i in days_to_show:
            date = start_date + timedelta(days=i)
            labels.append(date.strftime('%b %d'))  # e.g., "Nov 13"
            date_ranges.append(date)
            
    elif period == '3m':
        start_date = end_date - relativedelta(months=3)
        # Monthly breakdown for 3 months
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%B %Y'))  # e.g., "November 2025"
            # Store first and last day of month
            last_day = calendar.monthrange(current.year, current.month)[1]
            month_start = current.replace(day=1)
            month_end = current.replace(day=last_day)
            date_ranges.append((month_start, month_end))
            current = current + relativedelta(months=1)
            
    elif period == '6m':
        start_date = end_date - relativedelta(months=6)
        # Monthly breakdown for 6 months
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%b %Y'))  # e.g., "Nov 2025"
            last_day = calendar.monthrange(current.year, current.month)[1]
            month_start = current.replace(day=1)
            month_end = current.replace(day=last_day)
            date_ranges.append((month_start, month_end))
            current = current + relativedelta(months=1)
            
    elif period == '1y':
        start_date = end_date - relativedelta(months=12)
        # Monthly breakdown for 1 year
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%b %Y'))  # e.g., "Nov 2025"
            last_day = calendar.monthrange(current.year, current.month)[1]
            month_start = current.replace(day=1)
            month_end = current.replace(day=last_day)
            date_ranges.append((month_start, month_end))
            current = current + relativedelta(months=1)
            
    elif period == '3y':
        start_date = end_date - relativedelta(years=3)
        # Yearly breakdown for 3 years
        for i in range(4):  # Include current year
            year = start_date.year + i
            labels.append(str(year))
            year_start = timezone.datetime(year, 1, 1).date()
            year_end = timezone.datetime(year, 12, 31).date()
            date_ranges.append((year_start, year_end))
            
    else:  # all
        start_date = None
        labels = ['All Time']
        date_ranges = [None]
    
    # Fetch data based on metric type
    data = []
    
    if metric_type == 'check_ins':
        if period == 'all':
            check_ins = GymCheckIn.objects.all()
            data = [check_ins.count()]
        elif period == '1d':
            # Hourly aggregation
            for hour_start, hour_end in date_ranges:
                count = GymCheckIn.objects.filter(
                    date=end_date,
                    check_in_time__hour__gte=hour_start,
                    check_in_time__hour__lt=hour_end
                ).count()
                data.append(count)
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    count = GymCheckIn.objects.filter(
                        date__gte=date_range[0],
                        date__lte=date_range[1]
                    ).count()
                else:
                    count = GymCheckIn.objects.filter(date=date_range).count()
                data.append(count)
        
    elif metric_type == 'revenue':
        if period == 'all':
            payments = Payment.objects.filter(status='Completed')
            total = payments.aggregate(total=Sum('amount'))['total'] or 0
            data = [float(total)]
        elif period == '1d':
            # Hourly aggregation
            for hour_start, hour_end in date_ranges:
                total = Payment.objects.filter(
                    payment_date__date=end_date,
                    payment_date__hour__gte=hour_start,
                    payment_date__hour__lt=hour_end,
                    status='Completed'
                ).aggregate(total=Sum('amount'))['total'] or 0
                data.append(float(total))
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    total = Payment.objects.filter(
                        payment_date__date__gte=date_range[0],
                        payment_date__date__lte=date_range[1],
                        status='Completed'
                    ).aggregate(total=Sum('amount'))['total'] or 0
                else:
                    total = Payment.objects.filter(
                        payment_date__date=date_range,
                        status='Completed'
                    ).aggregate(total=Sum('amount'))['total'] or 0
                data.append(float(total))
        
    elif metric_type == 'new_members':
        if period == 'all':
            members = Member.objects.filter(is_deleted=False)
            data = [members.count()]
        elif period == '1d':
            # Hourly aggregation
            for hour_start, hour_end in date_ranges:
                count = Member.objects.filter(
                    date_created__date=end_date,
                    date_created__hour__gte=hour_start,
                    date_created__hour__lt=hour_end,
                    is_deleted=False
                ).count()
                data.append(count)
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    count = Member.objects.filter(
                        date_created__date__gte=date_range[0],
                        date_created__date__lte=date_range[1],
                        is_deleted=False
                    ).count()
                else:
                    count = Member.objects.filter(
                        date_created__date=date_range,
                        is_deleted=False
                    ).count()
                data.append(count)
        
    elif metric_type == 'active_members':
        # Use snapshots for historical data, real-time for recent dates
        for date_range in date_ranges:
            if isinstance(date_range, tuple):
                # For ranges, get snapshot from end of range
                target_date = date_range[1]
            else:
                target_date = date_range
            
            # Try to get from snapshot first
            snapshot = ActiveMemberSnapshot.objects.filter(date=target_date).first()
            
            if snapshot:
                count = snapshot.active_count
            else:
                # Calculate on the fly if snapshot doesn't exist
                count = Member.objects.filter(
                    is_active=True,
                    is_deleted=False,
                    start_date__lte=target_date,
                    end_date__gte=target_date
                ).count()
            
            data.append(count)
        
    elif metric_type == 'payment_methods':
        if period == 'all':
            payments = Payment.objects.filter(status='Completed')
        elif isinstance(date_ranges[0], tuple):
            payments = Payment.objects.filter(
                payment_date__date__gte=date_ranges[0][0],
                payment_date__date__lte=date_ranges[-1][1] if isinstance(date_ranges[-1], tuple) else date_ranges[-1],
                status='Completed'
            )
        else:
            payments = Payment.objects.filter(
                payment_date__date__gte=date_ranges[0],
                payment_date__date__lte=date_ranges[-1],
                status='Completed'
            )
        
        method_counts = payments.values('payment_method').annotate(count=Count('id')).order_by('-count')
        labels = [item['payment_method'] for item in method_counts]
        data = [item['count'] for item in method_counts]
    
    elif metric_type == 'retention_rate':
        # Calculate retention rate: (members who renewed / members who could have renewed) * 100
        for date_range in date_ranges:
            if isinstance(date_range, tuple):
                start, end = date_range
                # Members whose membership expired in this period
                expired = Member.objects.filter(
                    is_deleted=False,
                    end_date__gte=start,
                    end_date__lte=end
                ).count()
                
                # Of those expired, how many have a payment after expiry (renewed)?
                renewed = 0
                for member in Member.objects.filter(is_deleted=False, end_date__gte=start, end_date__lte=end):
                    # Check if they have payments after their end_date
                    renewal_payment = Payment.objects.filter(
                        member=member,
                        payment_date__date__gt=member.end_date,
                        status='Completed'
                    ).exists()
                    if renewal_payment:
                        renewed += 1
                
                rate = (renewed / expired * 100) if expired > 0 else 0
                data.append(round(rate, 2))
            else:
                # For single dates, calculate retention for members expiring on that date
                expired = Member.objects.filter(
                    is_deleted=False,
                    end_date=date_range
                ).count()
                
                renewed = 0
                for member in Member.objects.filter(is_deleted=False, end_date=date_range):
                    renewal_payment = Payment.objects.filter(
                        member=member,
                        payment_date__date__gt=member.end_date,
                        status='Completed'
                    ).exists()
                    if renewal_payment:
                        renewed += 1
                
                rate = (renewed / expired * 100) if expired > 0 else 0
                data.append(round(rate, 2))
    
    elif metric_type == 'churn_rate':
        # Churn rate: (members who didn't renew / total members who could renew) * 100
        for date_range in date_ranges:
            if isinstance(date_range, tuple):
                start, end = date_range
                expired = Member.objects.filter(
                    is_deleted=False,
                    end_date__gte=start,
                    end_date__lte=end
                ).count()
                
                churned = 0
                for member in Member.objects.filter(is_deleted=False, end_date__gte=start, end_date__lte=end):
                    renewal_payment = Payment.objects.filter(
                        member=member,
                        payment_date__date__gt=member.end_date,
                        status='Completed'
                    ).exists()
                    if not renewal_payment:
                        churned += 1
                
                rate = (churned / expired * 100) if expired > 0 else 0
                data.append(round(rate, 2))
            else:
                expired = Member.objects.filter(
                    is_deleted=False,
                    end_date=date_range
                ).count()
                
                churned = 0
                for member in Member.objects.filter(is_deleted=False, end_date=date_range):
                    renewal_payment = Payment.objects.filter(
                        member=member,
                        payment_date__date__gt=member.end_date,
                        status='Completed'
                    ).exists()
                    if not renewal_payment:
                        churned += 1
                
                rate = (churned / expired * 100) if expired > 0 else 0
                data.append(round(rate, 2))
    
    elif metric_type == 'revenue_per_member':
        # Average revenue per active member
        for date_range in date_ranges:
            if isinstance(date_range, tuple):
                start, end = date_range
                total_revenue = Payment.objects.filter(
                    payment_date__date__gte=start,
                    payment_date__date__lte=end,
                    status='Completed'
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                # Average active members during this period
                snapshot = ActiveMemberSnapshot.objects.filter(date__gte=start, date__lte=end)
                if snapshot.exists():
                    avg_members = snapshot.aggregate(avg=Avg('active_count'))['avg'] or 1
                else:
                    avg_members = Member.objects.filter(
                        is_active=True,
                        is_deleted=False,
                        start_date__lte=end,
                        end_date__gte=start
                    ).count() or 1
                
                rpm = float(total_revenue) / avg_members if avg_members > 0 else 0
                data.append(round(rpm, 2))
            else:
                total_revenue = Payment.objects.filter(
                    payment_date__date=date_range,
                    status='Completed'
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                active_members = Member.objects.filter(
                    is_active=True,
                    is_deleted=False,
                    start_date__lte=date_range,
                    end_date__gte=date_range
                ).count() or 1
                
                rpm = float(total_revenue) / active_members if active_members > 0 else 0
                data.append(round(rpm, 2))
    
    elif metric_type == 'avg_session_duration':
        # Average gym session duration in minutes
        for date_range in date_ranges:
            if isinstance(date_range, tuple):
                start, end = date_range
                sessions = GymCheckIn.objects.filter(
                    date__gte=start,
                    date__lte=end,
                    check_out_time__isnull=False
                )
            else:
                sessions = GymCheckIn.objects.filter(
                    date=date_range,
                    check_out_time__isnull=False
                )
            
            if sessions.exists():
                total_duration = 0
                count = 0
                for session in sessions:
                    if session.check_out_time and session.check_in_time:
                        duration = (session.check_out_time - session.check_in_time).total_seconds() / 60
                        total_duration += duration
                        count += 1
                
                avg_duration = total_duration / count if count > 0 else 0
                data.append(round(avg_duration, 2))
            else:
                data.append(0)
    
    # Calculate dynamic scale for better visualization
    scale = calculate_dynamic_scale(data)
    
    return JsonResponse({
        'labels': labels,
        'data': data,
        'metric': metric_type,
        'period': period,
        'scale': scale
    })
