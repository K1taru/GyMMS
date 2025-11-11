# GyMMS Dashboard Guide

## Overview
The GyMMS Dashboard provides real-time statistics and insights about your gym operations, including member check-ins, revenue tracking, and activity monitoring.

## Features

### 📊 Key Statistics (Top Cards)

1. **Daily Walk-ins**
   - Shows the count of unique members who checked in today
   - Helps track daily foot traffic
   - Updates in real-time with each new check-in

2. **Monthly Check-ins**
   - Total number of member visits this month
   - Useful for tracking monthly engagement
   - Resets at the start of each month

3. **Today's Revenue**
   - Total revenue collected today from completed payments
   - Shows monthly revenue in the subtitle
   - Only counts payments with "Completed" status

4. **Currently Active**
   - Number of members currently in the gym
   - Members who checked in but haven't checked out yet
   - Real-time indicator of gym capacity

### 📋 Recent Check-ins

- Displays the last 10 member check-ins
- Shows member avatars (initials)
- Displays check-in time (e.g., "5 minutes ago")
- Shows duration if member has checked out
- Status indicator: "In Gym" (green) or "Checked Out" (gray)

### 📈 Quick Stats Sidebar

1. **Active Members**
   - Total number of active memberships
   - Members with current, non-expired memberships

2. **Expiring Soon**
   - Count of memberships expiring within 7 days
   - Helps identify members who need renewal reminders
   - Alert-style card (red accent)

3. **New This Month**
   - New member registrations this month
   - Tracks growth and acquisition

### 📊 Peak Hours Chart

- Visual bar chart showing check-in distribution by hour
- Helps identify busiest times of the day
- Useful for staff scheduling and resource allocation
- Animated on page load

### 🕐 Live Clock

- Real-time clock in the header
- Updates every second
- Shows current date and time
- Visual "live" indicator (pulsing red dot)

## Models

### GymCheckIn
Tracks when members enter and leave the gym.

**Fields:**
- `member` - Reference to the Member
- `check_in_time` - When member entered
- `check_out_time` - When member left (null if still in gym)
- `date` - Date of check-in (for easy filtering)

**Properties:**
- `duration` - Calculates time spent in gym

### DashboardStats
Caches daily statistics for performance optimization.

**Fields:**
- `date` - The date for these statistics
- `daily_walk_ins` - Unique members who visited
- `total_check_ins` - Total check-in events
- `total_revenue` - Revenue collected that day
- `active_members` - Count of active memberships
- `new_members` - New registrations that day

## Setup Instructions

### 1. Run Migrations
```bash
# If using Docker:
docker-compose exec web python manage.py makemigrations dashboard
docker-compose exec web python manage.py migrate

# If using local Python:
python manage.py makemigrations dashboard
python manage.py migrate
```

### 2. Create Sample Data (Optional)
To test the dashboard with sample data:

```python
# In Django shell (python manage.py shell)
from dashboard.models import GymCheckIn
from memberships.models import Member
from django.utils import timezone

# Create a check-in for a member
member = Member.objects.first()
GymCheckIn.objects.create(
    member=member,
    check_in_time=timezone.now(),
    date=timezone.now().date()
)
```

### 3. Admin Interface
Access the admin panel to manage check-ins:
- Navigate to `/admin`
- Go to "Gym Check Ins" to view/edit check-ins
- Go to "Dashboard Stats" to view cached statistics

## Usage Guide

### Recording Check-ins

You'll need to create views/endpoints for staff to record member check-ins and check-outs. Example:

```python
# In dashboard/views.py
@login_required
def check_in_member(request, member_id):
    member = Member.objects.get(id=member_id)
    check_in = GymCheckIn.objects.create(
        member=member,
        check_in_time=timezone.now(),
        date=timezone.now().date()
    )
    return redirect('dashboard:dashboard')

@login_required
def check_out_member(request, check_in_id):
    check_in = GymCheckIn.objects.get(id=check_in_id)
    check_in.check_out_time = timezone.now()
    check_in.save()
    return redirect('dashboard:dashboard')
```

### Responsive Design

The dashboard is fully responsive:
- **Desktop (>1024px)**: 4 stat cards in a row, 2-column layout
- **Tablet (768-1024px)**: 2 stat cards in a row
- **Mobile (<768px)**: 1 stat card per row, stacked layout

### Performance Optimization

For large gyms with many check-ins, consider:

1. **Implement Caching**
```python
from django.core.cache import cache

def dashboard(request):
    cache_key = f'dashboard_stats_{today}'
    stats = cache.get(cache_key)
    
    if not stats:
        # Calculate stats
        stats = {...}
        cache.set(cache_key, stats, 300)  # Cache for 5 minutes
```

2. **Use DashboardStats Model**
Create a management command to cache daily stats:
```python
# dashboard/management/commands/cache_daily_stats.py
from django.core.management.base import BaseCommand
from dashboard.models import DashboardStats

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Calculate and save today's stats
        DashboardStats.objects.update_or_create(...)
```

## Customization

### Adding New Statistics

1. **Add to View**
```python
# In dashboard/views.py
new_stat = SomeModel.objects.filter(...).count()
context['new_stat'] = new_stat
```

2. **Add to Template**
```html
<div class="stat-card">
    <div class="stat-header">
        <div>
            <div class="stat-label">New Stat</div>
            <div class="stat-value">{{ new_stat }}</div>
        </div>
        <div class="stat-icon">🎯</div>
    </div>
</div>
```

### Changing Colors

Edit `dashboard/static/dashboard/css/dashboard.css`:

```css
.stat-card.your-class {
    border-left-color: #your-color;
}
```

### Modifying Refresh Interval

In `dashboard/static/dashboard/js/dashboard.js`:

```javascript
// Uncomment and modify
setInterval(refreshDashboardData, 60000); // 60000ms = 1 minute
```

## Troubleshooting

### No Data Showing
- Ensure migrations are applied
- Check if there are any members in the database
- Verify check-in records exist for today

### Clock Not Updating
- Check browser console for JavaScript errors
- Ensure `dashboard.js` is loading correctly
- Verify the `currentTime` element exists in HTML

### Statistics Incorrect
- Check database queries in `views.py`
- Verify timezone settings in `settings.py`
- Check that related models (Member, Payment) have data

### Styling Issues
- Ensure CSS file is loading (check Network tab)
- Verify CSS variables are defined in `core/css/index.css`
- Check for CSS conflicts with other stylesheets

## Future Enhancements

Potential features to add:
- Real-time updates using WebSockets
- Export statistics to PDF/Excel
- Member attendance heatmap
- Revenue trends chart
- Member birthday notifications
- Automatic membership expiry emails
- QR code check-in system
- Mobile app integration

## API Integration (Optional)

For a mobile app or external integrations, consider creating REST API endpoints:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def dashboard_stats_api(request):
    # Return JSON statistics
    return Response({
        'daily_walk_ins': daily_walk_ins,
        'active_in_gym': active_in_gym,
        # ... other stats
    })
```

## Security Considerations

- All dashboard views are protected with `@login_required`
- Only authenticated staff can access the dashboard
- Check-in/check-out actions should verify staff permissions
- Consider adding role-based access (Owner vs Staff)

## Support

For issues or questions:
1. Check the Django logs
2. Review the browser console for JavaScript errors
3. Verify database connections
4. Ensure all static files are collected (`collectstatic`)
