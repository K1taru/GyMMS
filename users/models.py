from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'admin'), 
        ('Member', 'member'),
    ]
    
    SEX_CHOICES = [
        ('Male', 'male', 'M', 'm'), 
        ('Female', 'female', 'F', 'f'),
    ]
    
    # Login & Basic User Requirements
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    # User Data & Information
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    age = models.PositiveIntegerField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='media/profiles/', null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    sex = models.CharField(max_length=10,choices=SEX_CHOICES, null=True, blank=True)
    
    # Security & Account Management
    date_created = models.DateTimeField(auto_now_add=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(null=True, blank=True)
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)


    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.last_password_change = timezone.now()

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def is_pending_permanent_delete(self):
        if not self.deleted_at:
            return False
        return timezone.now() >= self.deleted_at + timedelta(days=7)

    def __str__(self):
        return f"{self.username} ({self.role})"
