from django.contrib.auth.models import UserManager


class StaffUserManager(UserManager):
    """Give manually provisioned superusers the application's Owner role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'Owner')
        extra_fields.setdefault('is_active', True)
        if extra_fields['role'] != 'Owner':
            raise ValueError('Superuser must have role=Owner.')
        if extra_fields['is_active'] is not True:
            raise ValueError('Superuser must have is_active=True.')
        return super().create_superuser(username, email, password, **extra_fields)
