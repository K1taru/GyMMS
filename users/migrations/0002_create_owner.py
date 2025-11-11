from django.db import migrations
from django.contrib.auth.hashers import make_password
from django.utils import timezone


def create_owner(apps, schema_editor):
    StaffUser = apps.get_model('users', 'StaffUser')
    
    # Create owner account if it doesn't exist
    if not StaffUser.objects.filter(username='owner123').exists():
        owner = StaffUser.objects.create(
            username='owner123',
            email='owner123@gmail.com',
            phone_number='09667405540',
            role='Owner',
            is_staff=True,
            is_superuser=True,
            is_active=True,
            password=make_password('GyMMS@2023'),
            is_email_verified=False,
            is_phone_verified=False,
            last_password_change=timezone.now(),
            created_by=None,
        )


def remove_owner(apps, schema_editor):
    StaffUser = apps.get_model('users', 'StaffUser')
    StaffUser.objects.filter(username='owner123').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Ensure auth is ready
    ]

    operations = [
        migrations.RunPython(create_owner, remove_owner),
    ]
