from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
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
    custom_date_from = request.GET.get('date_from', '')
    custom_date_to = request.GET.get('date_to', '')
    
    # Calculate date range and labels based on period or custom dates
    end_date = timezone.now().date()
    labels = []
    date_ranges = []
    
    # Handle custom date range
    if custom_date_from or custom_date_to:
        try:
            if custom_date_from:
                start_date = timezone.datetime.strptime(custom_date_from, '%Y-%m-%d').date()
            else:
                start_date = end_date - timedelta(days=30)
                
            if custom_date_to:
                end_date = timezone.datetime.strptime(custom_date_to, '%Y-%m-%d').date()
            else:
                end_date = timezone.now().date()
            
            # Determine granularity based on date range
            days_diff = (end_date - start_date).days
            
            if days_diff <= 1:
                # Hourly for same day or 1 day
                for hour in range(0, 24, 4):
                    period = 'AM' if hour < 12 else 'PM'
                    display_hour = hour if hour <= 12 else hour - 12
                    display_hour = 12 if display_hour == 0 else display_hour
                    labels.append(f'{display_hour}{period}')
                    date_ranges.append((hour, hour + 4))
            elif days_diff <= 7:
                # Daily for up to a week
                current = start_date
                while current <= end_date:
                    labels.append(current.strftime('%a %d'))
                    date_ranges.append(current)
                    current += timedelta(days=1)
            elif days_diff <= 90:
                # Daily for up to 3 months (show every 3 days)
                current = start_date
                while current <= end_date:
                    labels.append(current.strftime('%b %d'))
                    date_ranges.append(current)
                    current += timedelta(days=3)
            else:
                # Weekly for longer periods (show every 7 days)
                current = start_date
                while current <= end_date:
                    labels.append(current.strftime('%b %d'))
                    date_ranges.append(current)
                    current += timedelta(days=7)
                    
        except ValueError:
            # Invalid date format, fall back to default period
            custom_date_from = ''
            custom_date_to = ''
    
    # Use predefined periods if no custom dates
    if not custom_date_from and not custom_date_to:
        end_date = timezone.now().date()
        
        if period == '1d':
            start_date = end_date
            # Hourly breakdown for 1 day - 24 hourly points
            for hour in range(24):
                period_label = 'AM' if hour < 12 else 'PM'
                display_hour = hour if hour <= 12 else hour - 12
                display_hour = 12 if display_hour == 0 else display_hour
                labels.append(f'{display_hour}{period_label}')
                date_ranges.append((hour, hour + 1))
                
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
            # Daily breakdown for 6 months (show every 3 days to keep chart readable)
            current = start_date
            while current <= end_date:
                labels.append(current.strftime('%b %d'))
                date_ranges.append(current)
                current += timedelta(days=3)
                
        elif period == '1y':
            start_date = end_date - relativedelta(months=12)
            # Weekly breakdown for 1 year (show every 7 days)
            current = start_date
            while current <= end_date:
                labels.append(current.strftime('%b %d'))
                date_ranges.append(current)
                current += timedelta(days=7)
                
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
            # For 'all', generate dynamic timeline from earliest to latest
            # This creates ups and downs showing progression over time
            # Labels and date_ranges will be populated by each metric's 'all time' logic
            start_date = None
            labels = []
            date_ranges = []
    
    # Fetch data based on metric type
    data = []
    
    # Determine if we're using hourly aggregation
    is_hourly = len(date_ranges) > 0 and isinstance(date_ranges[0], tuple) and isinstance(date_ranges[0][0], int)
    
    if metric_type == 'check_ins':
        if not date_ranges or (len(date_ranges) == 0):
            # All time - get compressed timeline with weekly aggregation
            first_checkin = GymCheckIn.objects.order_by('date').first()
            if first_checkin:
                start_date = first_checkin.date
                end_date = timezone.now().date()
                # Sample every week with range aggregation
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    count = GymCheckIn.objects.filter(
                        date__gte=current,
                        date__lte=week_end
                    ).count()
                    data.append(count)
                    current += timedelta(days=7)
            else:
                # If no check-ins exist, show empty chart with message
                labels = ['No Check-ins Yet']
                data = [0]
        elif is_hourly:
            # Hourly aggregation for single day
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
    
    elif metric_type == 'walk_ins':
        # Walk-ins are guest payments (GYMMSGUEST)
        if not date_ranges or (len(date_ranges) == 0):
            # All time - get compressed timeline with weekly aggregation
            first_payment = Payment.objects.filter(
                stored_member_id='GYMMSGUEST',
                status='Completed'
            ).order_by('payment_date').first()
            if first_payment:
                start_date = first_payment.payment_date.date()
                end_date = timezone.now().date()
                # Sample every week with range aggregation
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    count = Payment.objects.filter(
                        payment_date__date__gte=current,
                        payment_date__date__lte=week_end,
                        stored_member_id='GYMMSGUEST',
                        status='Completed'
                    ).count()
                    data.append(count)
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # Hourly walk-ins for single day
            for hour_start, hour_end in date_ranges:
                count = Payment.objects.filter(
                    payment_date__date=end_date,
                    payment_date__hour__gte=hour_start,
                    payment_date__hour__lt=hour_end,
                    stored_member_id='GYMMSGUEST',
                    status='Completed'
                ).count()
                data.append(count)
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    count = Payment.objects.filter(
                        payment_date__date__gte=date_range[0],
                        payment_date__date__lte=date_range[1],
                        stored_member_id='GYMMSGUEST',
                        status='Completed'
                    ).count()
                else:
                    count = Payment.objects.filter(
                        payment_date__date=date_range,
                        stored_member_id='GYMMSGUEST',
                        status='Completed'
                    ).count()
                data.append(count)
        
    elif metric_type == 'revenue':
        if not date_ranges or (len(date_ranges) == 0):
            # All time - get compressed timeline with weekly aggregation
            first_payment = Payment.objects.filter(status='Completed').order_by('payment_date').first()
            if first_payment:
                start_date = first_payment.payment_date.date()
                end_date = timezone.now().date()
                # Sample every week with range aggregation
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    total = Payment.objects.filter(
                        payment_date__date__gte=current,
                        payment_date__date__lte=week_end,
                        status='Completed'
                    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                    data.append(float(total))
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # Hourly aggregation for single day
            for hour_start, hour_end in date_ranges:
                total = Payment.objects.filter(
                    payment_date__date=end_date,
                    payment_date__hour__gte=hour_start,
                    payment_date__hour__lt=hour_end,
                    status='Completed'
                ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                data.append(float(total))
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    total = Payment.objects.filter(
                        payment_date__date__gte=date_range[0],
                        payment_date__date__lte=date_range[1],
                        status='Completed'
                    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                else:
                    total = Payment.objects.filter(
                        payment_date__date=date_range,
                        status='Completed'
                    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                data.append(float(total))
        
    elif metric_type == 'new_members':
        if not date_ranges or (len(date_ranges) == 0):
            # All time - get compressed timeline with weekly aggregation
            first_member = Member.objects.filter(is_deleted=False).order_by('date_created').first()
            if first_member:
                start_date = first_member.date_created.date()
                end_date = timezone.now().date()
                # Sample every week with range aggregation
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    count = Member.objects.filter(
                        date_created__date__gte=current,
                        date_created__date__lte=week_end,
                        is_deleted=False
                    ).count()
                    data.append(count)
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # Hourly aggregation for single day
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
        if not date_ranges or (len(date_ranges) == 0):
            # All time - get compressed timeline with weekly sampling
            first_member = Member.objects.filter(is_deleted=False).order_by('date_created').first()
            if first_member:
                start_date = first_member.date_created.date()
                end_date = timezone.now().date()
                # Sample every week - check active count at end of each week
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    
                    # Get active members at the end of the week
                    snapshot = ActiveMemberSnapshot.objects.filter(date=week_end).first()
                    if snapshot:
                        count = snapshot.active_count
                    else:
                        count = Member.objects.filter(
                            is_active=True,
                            is_deleted=False,
                            start_date__lte=week_end,
                            end_date__gte=week_end
                        ).count()
                    data.append(count)
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # For hourly on 1D, show current active member count for each hour
            # Active members don't change hourly, so we show the daily count
            count = Member.objects.filter(
                is_active=True,
                is_deleted=False,
                start_date__lte=end_date,
                end_date__gte=end_date
            ).count()
            for _ in date_ranges:
                data.append(count)
        else:
            # Use snapshots for historical data, real-time for recent dates
            for date_range in date_ranges:
                # Extract the actual date from tuple or use date directly
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
        if not date_ranges or not date_ranges[0]:
            # All time
            payments = Payment.objects.filter(status='Completed')
        elif is_hourly:
            # For hourly, get all payments on that date
            payments = Payment.objects.filter(
                payment_date__date=end_date,
                status='Completed'
            )
        elif isinstance(date_ranges[0], tuple) and len(date_ranges[0]) == 2 and isinstance(date_ranges[0][0], int):
            # Skip hourly tuples
            payments = Payment.objects.filter(status='Completed')
        else:
            # Date-based filtering
            first_date = date_ranges[0] if not isinstance(date_ranges[0], tuple) else date_ranges[0][0]
            last_date = date_ranges[-1] if not isinstance(date_ranges[-1], tuple) else date_ranges[-1][1]
            payments = Payment.objects.filter(
                payment_date__date__gte=first_date,
                payment_date__date__lte=last_date,
                status='Completed'
            )
        
        method_counts = payments.values('payment_method').annotate(count=Count('id')).order_by('-count')
        labels = [item['payment_method'] for item in method_counts]
        data = [item['count'] for item in method_counts]
    
    elif metric_type == 'member_check_ins':
        # Total check-ins (walk-ins + member check-ins)
        if not date_ranges or (len(date_ranges) == 0):
            # All time - compressed timeline with weekly aggregation
            first_checkin = GymCheckIn.objects.order_by('date').first()
            first_walkin = Payment.objects.filter(
                stored_member_id='GYMMSGUEST',
                status='Completed'
            ).order_by('payment_date').first()
            
            earliest_date = None
            if first_checkin and first_walkin:
                earliest_date = min(first_checkin.date, first_walkin.payment_date.date())
            elif first_checkin:
                earliest_date = first_checkin.date
            elif first_walkin:
                earliest_date = first_walkin.payment_date.date()
            
            if earliest_date:
                start_date = earliest_date
                end_date = timezone.now().date()
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    
                    # Member check-ins
                    member_checkins = GymCheckIn.objects.filter(
                        date__gte=current,
                        date__lte=week_end
                    ).count()
                    
                    # Walk-ins from Payment
                    walk_ins = Payment.objects.filter(
                        payment_date__date__gte=current,
                        payment_date__date__lte=week_end,
                        stored_member_id='GYMMSGUEST',
                        status='Completed'
                    ).count()
                    
                    total = member_checkins + walk_ins
                    data.append(total)
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # For hourly, we aggregate both
            for hour_start, hour_end in date_ranges:
                member_checkins = GymCheckIn.objects.filter(
                    date=end_date,
                    check_in_time__hour__gte=hour_start,
                    check_in_time__hour__lt=hour_end
                ).count()
                
                # Walk-ins from payments in this hour
                walk_ins = Payment.objects.filter(
                    payment_date__date=end_date,
                    payment_date__hour__gte=hour_start,
                    payment_date__hour__lt=hour_end,
                    stored_member_id='GYMMSGUEST',
                    status='Completed'
                ).count()
                
                total = member_checkins + walk_ins
                data.append(total)
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    member_checkins = GymCheckIn.objects.filter(
                        date__gte=date_range[0],
                        date__lte=date_range[1]
                    ).count()
                    
                    walk_ins = Payment.objects.filter(
                        payment_date__date__gte=date_range[0],
                        payment_date__date__lte=date_range[1],
                        stored_member_id='GYMMSGUEST',
                        status='Completed'
                    ).count()
                else:
                    member_checkins = GymCheckIn.objects.filter(date=date_range).count()
                    
                    walk_ins = Payment.objects.filter(
                        payment_date__date=date_range,
                        stored_member_id='GYMMSGUEST',
                        status='Completed'
                    ).count()
                
                total = member_checkins + walk_ins
                data.append(total)
    
    elif metric_type == 'total_transactions':
        # Total transaction count (all completed payments)
        if not date_ranges or (len(date_ranges) == 0):
            # All time - compressed timeline with weekly aggregation
            first_payment = Payment.objects.filter(status='Completed').order_by('payment_date').first()
            if first_payment:
                start_date = first_payment.payment_date.date()
                end_date = timezone.now().date()
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    count = Payment.objects.filter(
                        payment_date__date__gte=current,
                        payment_date__date__lte=week_end,
                        status='Completed'
                    ).count()
                    data.append(count)
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # Hourly transaction count for single day
            for hour_start, hour_end in date_ranges:
                count = Payment.objects.filter(
                    payment_date__date=end_date,
                    payment_date__hour__gte=hour_start,
                    payment_date__hour__lt=hour_end,
                    status='Completed'
                ).count()
                data.append(count)
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    count = Payment.objects.filter(
                        payment_date__date__gte=date_range[0],
                        payment_date__date__lte=date_range[1],
                        status='Completed'
                    ).count()
                else:
                    count = Payment.objects.filter(
                        payment_date__date=date_range,
                        status='Completed'
                    ).count()
                data.append(count)
    
    elif metric_type == 'revenue_per_member':
        if not date_ranges or not date_ranges[0]:
            # All time - dynamic timeline with weekly aggregation
            first_payment = Payment.objects.filter(status='Completed').order_by('payment_date').first()
            first_member = Member.objects.filter(is_deleted=False).order_by('date_created').first()
            
            if first_payment or first_member:
                # Use earliest date from either payments or members
                start_dates = []
                if first_payment:
                    start_dates.append(first_payment.payment_date.date())
                if first_member:
                    start_dates.append(first_member.date_created.date())
                
                start_date = min(start_dates)
                end_date = timezone.now().date()
                
                # Sample every week with range aggregation
                current = start_date
                while current <= end_date:
                    week_end = min(current + timedelta(days=6), end_date)
                    labels.append(current.strftime('%b %d, %Y'))
                    
                    # Revenue during this week
                    total_revenue = Payment.objects.filter(
                        payment_date__date__gte=current,
                        payment_date__date__lte=week_end,
                        status='Completed'
                    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                    
                    # Active members at end of week
                    active_members = Member.objects.filter(
                        is_active=True,
                        is_deleted=False,
                        start_date__lte=week_end,
                        end_date__gte=week_end
                    ).count() or 1
                    
                    rpm = float(total_revenue) / active_members if active_members > 0 else 0
                    data.append(round(rpm, 2))
                    current += timedelta(days=7)
            else:
                labels = ['No Data']
                data = [0]
        elif is_hourly:
            # For hourly, aggregate for the whole day
            total_revenue = Payment.objects.filter(
                payment_date__date=end_date,
                status='Completed'
            ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
            active_members = Member.objects.filter(
                is_active=True,
                is_deleted=False,
                start_date__lte=end_date,
                end_date__gte=end_date
            ).count() or 1
            rpm = float(total_revenue) / active_members if active_members > 0 else 0
            # Repeat for each hour slot
            for _ in date_ranges:
                data.append(round(rpm, 2))
        else:
            # Date-based aggregation
            for date_range in date_ranges:
                if isinstance(date_range, tuple):
                    start, end = date_range
                    total_revenue = Payment.objects.filter(
                        payment_date__date__gte=start,
                        payment_date__date__lte=end,
                        status='Completed'
                    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                    
                    # Average active members during this period
                    snapshot = ActiveMemberSnapshot.objects.filter(date__gte=start, date__lte=end)
                    if snapshot.exists():
                        avg_members = snapshot.aggregate(avg=Coalesce(Avg('active_count'), Decimal('1.00')))['avg']
                    else:
                        avg_members = Member.objects.filter(
                            is_active=True,
                            is_deleted=False,
                            start_date__lte=end,
                            end_date__gte=start
                        ).count() or 1
                    
                    rpm = float(total_revenue) / float(avg_members) if avg_members > 0 else 0
                    data.append(round(rpm, 2))
                else:
                    total_revenue = Payment.objects.filter(
                        payment_date__date=date_range,
                        status='Completed'
                    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
                    
                    active_members = Member.objects.filter(
                        is_active=True,
                        is_deleted=False,
                        start_date__lte=date_range,
                        end_date__gte=date_range
                    ).count() or 1
                    
                    rpm = float(total_revenue) / active_members if active_members > 0 else 0
                    data.append(round(rpm, 2))
    
    # Calculate dynamic scale for better visualization
    scale = calculate_dynamic_scale(data)
    
    return JsonResponse({
        'labels': labels,
        'data': data,
        'metric': metric_type,
        'period': period,
        'scale': scale
    })
