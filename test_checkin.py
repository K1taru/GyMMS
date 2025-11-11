"""
Quick test script to verify GymCheckIn model and database
Run this with: python manage.py shell < test_checkin.py
"""

print("=" * 50)
print("TESTING GYM CHECK-IN FUNCTIONALITY")
print("=" * 50)

# Import models
from dashboard.models import GymCheckIn
from memberships.models import Member
from django.utils import timezone

# Check if table exists and count records
print("\n1. Checking GymCheckIn table...")
try:
    total_checkins = GymCheckIn.objects.count()
    print(f"   ✓ Table exists with {total_checkins} total records")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check today's check-ins
print("\n2. Checking today's check-ins...")
try:
    today = timezone.now().date()
    today_checkins = GymCheckIn.objects.filter(date=today)
    print(f"   ✓ Found {today_checkins.count()} check-ins today")
    
    if today_checkins.exists():
        print("\n   Recent check-ins:")
        for checkin in today_checkins[:5]:
            print(f"   - {checkin.member.name} at {checkin.check_in_time.strftime('%H:%M')}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check active members
print("\n3. Checking active members...")
try:
    active_members = Member.objects.filter(
        is_deleted=False,
        is_active=True,
        end_date__gte=today
    )
    print(f"   ✓ Found {active_members.count()} active members")
    
    if active_members.exists():
        print("\n   Sample active members:")
        for member in active_members[:3]:
            print(f"   - {member.name} ({member.member_id}) - Expires: {member.end_date}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
