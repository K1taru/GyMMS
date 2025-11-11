from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Payment(models.Model):
    """
    Payment records for gym memberships
    Stores member info to preserve data even if member is deleted
    """
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('Maya', 'Maya'),
        ('GoTyme', 'GoTyme'),
        ('Bank Transfer', 'Bank Transfer'),
        ('PayPal', 'PayPal'),
        ('Debit Card', 'Debit Card'),
        ('Credit Card', 'Credit Card'),
    ]
    
    # Digital payment methods that require reference numbers
    DIGITAL_PAYMENT_METHODS = ['GCash', 'Maya', 'GoTyme', 'Bank Transfer', 'PayPal', 'Debit Card', 'Credit Card']
    
    PAYMENT_STATUS = [
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    # UUID primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Member reference (nullable to preserve payment history if member deleted)
    member = models.ForeignKey(
        'memberships.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        db_column='member_fk_id'  # Avoid clash with stored_member_id
    )
    
    # Stored member information (preserved even if member deleted)
    stored_member_id = models.CharField(max_length=10, default='UNKNOWN', help_text='Member ID at time of payment', db_index=True)
    stored_member_name = models.CharField(max_length=150, default='Unknown Member', help_text='Member name at time of payment')
    
    # Membership plan reference (nullable to preserve payment history if plan deleted)
    membership_plan = models.ForeignKey(
        'MembershipPricing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text='The pricing plan purchased'
    )
    
    # Stored pricing information (preserved even if plan modified/deleted)
    stored_plan_label = models.CharField(max_length=50, default='Unknown Plan', help_text='Plan label at time of payment')
    stored_duration_days = models.IntegerField(default=0, help_text='Duration in days at time of payment')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Reference number for GCash, Maya, or Bank Transfer'
    )
    payment_date = models.DateTimeField(default=timezone.now)
    
    # Status and processing
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='Completed'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_payments'
    )
    
    # Additional information
    remarks = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['stored_member_id']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.stored_member_name} ({self.stored_member_id})"


class MembershipPricing(models.Model):
    """
    Global pricing configuration for memberships
    Can only be modified by the owner
    """
    duration_days = models.IntegerField(
        help_text='Duration in days (e.g., 30 for monthly, 90 for quarterly)'
    )
    duration_label = models.CharField(
        max_length=50,
        help_text='Display label (e.g., "1 Month", "3 Months")'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price for this duration'
    )
    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['duration_days']
        verbose_name = 'Membership Pricing'
        verbose_name_plural = 'Membership Pricing'
    
    def __str__(self):
        return f"{self.duration_label} - ₱{self.price}"
