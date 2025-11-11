from django.db import models
from django.conf import settings
from django.utils import timezone
import os


def member_photo_path(instance, filename):
    """
    Generate upload path for member photos
    Format: member_photos/{member_id}.{ext}
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.member_id}.{ext}"
    return os.path.join('member_photos', filename)


class Member(models.Model):
    """
    Member model representing gym members
    """
    SEX_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    
    # Basic Information
    member_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        help_text='Auto-generated unique member ID'
    )
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, blank=True, null=True)
    address = models.TextField()
    
    # Photo
    photo = models.ImageField(upload_to=member_photo_path, blank=True, null=True)
    
    # Emergency Contact
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=15)
    
    # Membership Details
    start_date = models.DateField()
    end_date = models.DateField()
    membership_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Monthly fee at the time of registration/renewal'
    )
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_members'
    )
    date_created = models.DateTimeField(auto_now_add=True)
    
    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.member_id})"
    
    def is_membership_active(self):
        """
        Check if the membership is still valid
        """
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
    
    def days_until_expiry(self):
        """
        Calculate days until membership expires
        Returns negative if already expired
        """
        today = timezone.now().date()
        return (self.end_date - today).days
    
    def is_expiring_soon(self, days=7):
        """
        Check if membership is expiring within specified days
        """
        days_left = self.days_until_expiry()
        return 0 <= days_left <= days
    
    class Meta:
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['member_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['end_date']),
        ]


class MembershipConfig(models.Model):
    """
    Global configuration for membership fees
    Can only be modified by the owner
    """
    membership_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Monthly membership fee that can only be modified by the owner'
    )
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Membership Configuration'
        verbose_name_plural = 'Membership Configuration'
    
    def __str__(self):
        return f"Membership Fee: ₱{self.membership_fee}"
