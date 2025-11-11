from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class StaffUser(AbstractUser):
    ROLE_CHOICES = [
        ('Owner', 'owner'),
        ('Staff', 'staff'),
    ]
    
    # Login & Basic Staff Requirements
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_staff',
        help_text='The owner who created this staff account'
    )
    
    # Security & Account Management
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.role == 'Staff' and (not self.created_by or self.created_by.role != 'Owner'):
            raise ValueError("Staff accounts can only be created by Owners")
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.last_password_change = timezone.now()

    def __str__(self):
        return f"{self.username} ({self.role})"
