# Metrics Dashboard

## Overview
The metrics dashboard provides comprehensive analytics and visualization for gym management data with dynamic graphs and intelligent scaling.

## Features

### Metrics Available
1. **Total Check-ins** - Track gym attendance over time
2. **Total Revenue** - Monitor income from memberships
3. **New Members** - Track member acquisition
4. **Active Members** - View active membership trends (now with historical data!)
5. **Retention Rate (%)** - Measure how many members renew their memberships
6. **Churn Rate (%)** - Track members who don't renew
7. **Revenue per Member** - Calculate average revenue per active member
8. **Avg Session Duration (min)** - Monitor average gym session length
9. **Payment Methods** - Distribution of payment types

### Graph Types
- **Bar Chart** - Great for comparing discrete periods
- **Line Chart** - Best for trends over time
- **Area Chart** - Emphasizes volume and trends
- **Donut Chart** - Perfect for payment method distribution

### Time Periods
- **1D** - Hourly breakdown for today
- **1W** - Daily breakdown for the last week
- **1M** - Daily breakdown for the last month
- **3M** - Monthly breakdown for 3 months
- **6M** - Monthly breakdown for 6 months
- **1Y** - Monthly breakdown for 1 year
- **3Y** - Yearly breakdown for 3 years
- **ALL** - All-time totals

## Dynamic Y-Axis Scaling
The dashboard uses intelligent scaling to prevent charts from always hitting peak values:
- Statistical analysis (mean, standard deviation)
- Smart padding (15-25% above max values)
- Adapts to data variance
- Rounds to nice numbers for readability

## Active Member Tracking
Active members are now tracked using daily snapshots (`ActiveMemberSnapshot` model):
- Enables historical trend analysis
- Shows ups and downs instead of flat lines
- Captures daily metrics automatically

### Management Command
Run daily snapshots using:
```bash
# Create snapshot for today only
python manage.py create_member_snapshots

# Create snapshots for the last 7 days
python manage.py create_member_snapshots --days 7

# Backfill snapshots for the last 30 days
python manage.py create_member_snapshots --backfill 30
```

### Setting Up Automated Snapshots
For production, set up a daily cron job or scheduled task:

**Linux/Mac (crontab):**
```bash
# Run daily at 11:59 PM
59 23 * * * cd /path/to/GyMMS && python manage.py create_member_snapshots
```

**Docker (add to docker-compose):**
You can create a separate service or use a scheduler like `django-crontab` or `celery-beat`.

## New Metrics Explained

### Retention Rate
Percentage of members who renewed their membership after expiry. Higher is better.
- Formula: `(members who renewed / members who expired) × 100`

### Churn Rate
Percentage of members who didn't renew after expiry. Lower is better.
- Formula: `(members who didn't renew / members who expired) × 100`

### Revenue per Member
Average revenue generated per active member in a period.
- Formula: `total revenue / average active members`
- Helps identify revenue trends independent of member count

### Average Session Duration
How long members spend at the gym on average (in minutes).
- Only counts sessions with check-out times
- Helps understand gym utilization patterns

## Database Model

### ActiveMemberSnapshot
Stores daily snapshots of key metrics:
- `date` - The snapshot date
- `active_count` - Number of active members
- `total_members` - Total non-deleted members
- `new_members_today` - New registrations
- `expired_today` - Memberships that expired
- `total_revenue_today` - Revenue collected
- `check_ins_today` - Total check-ins

## Usage Tips
1. **Compare metrics side-by-side** - Use different time periods to spot trends
2. **Use appropriate graph types** - Line charts for trends, bar charts for comparisons
3. **Monitor retention/churn** - Key indicators of business health
4. **Track revenue per member** - Understand revenue quality, not just quantity
5. **Backfill historical data** - Run backfill command after setup to populate past data

## Technical Notes
- Uses Chart.js for visualization
- Dynamic AJAX data loading
- Statistical scaling for better UX
- Calendar-accurate date aggregation
- Optimized queries with database indexes
