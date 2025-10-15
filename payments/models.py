from django.db import models
from django.conf import settings
import uuid

from django.db.models.signals import pre_save
from django.dispatch import receiver
from membership_plans.models import Membership_Plan

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('GooglePay', 'Google Pay'),
        ('ApplePay', 'Apple Pay'),
        ('GCash', 'GCash'),
        ('GoTyme', 'GoTyme'),
        ('PayPal', 'PayPal'),
        ('Maya', 'Maya'),
        ('InstaPay', 'InstaPay'),
        ('Cash', 'Cash (Manual Payment)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'member'},
        related_name='payments'
    )
    membership_type = models.ForeignKey(
        'membership_plans.Membership_Plan', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    remarks = models.TextField(blank=True, null=True)
    processed_by_admin = models.BooleanField(default=False)  # True if admin marked as paid manually in cash

    def __str__(self):
        return f"Payment {self.id} - {self.member.username}"
