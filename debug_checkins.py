"""
Debug script to check GymCheckIn records
Run with: python manage.py shell < debug_checkins.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import GymCheckIn
from memberships.models import Member
from django.utils import timezone

print("=" * 60)
print("CHECKING GYM CHECK-IN DATABASE")
print("=" * 60)

# 1. Check total check-ins
total = GymCheckIn.objects.count()
print(f"\n1. Total check-ins in database: {total}")

# 2. Check today's check-ins
today = timezone.now().date()
today_checkins = GymCheckIn.objects.filter(date=today)
print(f"\n2. Today's check-ins ({today}): {today_checkins.count()}")

if today_checkins.exists():
    print("\n   Recent check-ins today:")
    for ci in today_checkins[:10]:
        print(f"   - ID: {ci.id}")
        print(f"     Member: {ci.member.name} ({ci.member.member_id})")
        print(f"     Time: {ci.check_in_time}")
        print(f"     Date: {ci.date}")
        print()

# 3. Check all check-ins (last 10)
print("\n3. Last 10 check-ins overall:")
all_checkins = GymCheckIn.objects.all()[:10]
for ci in all_checkins:
    print(f"   - {ci.member.name} on {ci.date} at {ci.check_in_time.strftime('%H:%M')}")

# 4. Check active members
print(f"\n4. Active members available: {Member.objects.filter(is_deleted=False, is_active=True).count()}")

# 5. Raw SQL check
from django.db import connection
print("\n5. Raw database check:")
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM dashboard_gymcheckin")
    row = cursor.fetchone()
    print(f"   Raw count from dashboard_gymcheckin table: {row[0]}")
    
    cursor.execute("SELECT id, member_id, check_in_time, date FROM dashboard_gymcheckin ORDER BY check_in_time DESC LIMIT 5")
    rows = cursor.fetchall()
    print(f"\n   Last 5 records:")
    for row in rows:
        print(f"   - ID: {row[0]}, Member: {row[1]}, Time: {row[2]}, Date: {row[3]}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
