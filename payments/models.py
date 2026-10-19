from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


PROCESSOR_SNAPSHOT_FIELDS = ('stored_processor_id', 'stored_processor_username', 'stored_processor_name')


def processor_snapshot(user):
    return dict(stored_processor_id=user.pk, stored_processor_username=user.username,
                stored_processor_name=(user.name or user.get_full_name())[:255])


class ProcessorSnapshot(models.Model):
    # Deliberately not a foreign key: attribution survives account deletion.
    stored_processor_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False, db_index=True)
    stored_processor_username = models.CharField(max_length=150, blank=True, editable=False)
    stored_processor_name = models.CharField(max_length=255, blank=True, editable=False)

    PROCESSOR_RELATION_FIELDS = ()

    class Meta:
        abstract = True

    @property
    def processor_display(self):
        if self.stored_processor_id is None:
            return 'Unknown processor'
        if self.stored_processor_name and self.stored_processor_username:
            return f'{self.stored_processor_name} ({self.stored_processor_username})'
        return self.stored_processor_username or self.stored_processor_name or f'Processor #{self.stored_processor_id}'

    def save(self, *args, **kwargs):
        fields = PROCESSOR_SNAPSHOT_FIELDS
        fields += self.PROCESSOR_RELATION_FIELDS
        if self._state.adding:
            actor = getattr(self, 'processed_by', None) or getattr(self, 'created_by', None)
            if self.stored_processor_id is None and actor:
                for field, value in processor_snapshot(actor).items():
                    setattr(self, field, value)
        else:
            update_fields = kwargs.get('update_fields')
            if update_fields is None or set(update_fields).intersection((*fields, 'processed_by')):
                original = type(self).objects.filter(pk=self.pk).values(*fields).first()
                if original and any(original[field] != getattr(self, field) for field in fields):
                    raise ValueError('Payment processor attribution is immutable.')
        super().save(*args, **kwargs)


class Payment(ProcessorSnapshot):
    """
    Payment records for gym memberships
    Stores member info to preserve data even if member is deleted
    """
    PROCESSOR_RELATION_FIELDS = ('processed_by_id',)

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('QRPh', 'QRPh'),
        ('GCash', 'GCash'),
        ('Maya', 'Maya'),
        ('GoTyme', 'GoTyme'),
        ('Bank Transfer', 'Bank Transfer'),
        ('PayPal', 'PayPal'),
        ('Debit Card', 'Debit Card'),
        ('Credit Card', 'Credit Card'),
    ]
    
    # Digital payment methods that require reference numbers
    DIGITAL_PAYMENT_METHODS = ['QRPh', 'GCash', 'Maya', 'GoTyme', 'Bank Transfer', 'PayPal', 'Debit Card', 'Credit Card']
    
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


UNRESOLVED_STATUSES = ('preparing', 'ready', 'processing', 'cancel_requested', 'needs_review')


class OnlinePaymentAttemptQuerySet(models.QuerySet):
    def blocking(self):
        return self.filter(status__in=UNRESOLVED_STATUSES, staff_cancelled_at__isnull=True)


class OnlinePaymentAttempt(ProcessorSnapshot):
    """A durable checkout, separate from the completed-payment ledger."""
    STATUS_CHOICES = [(s, s.replace('_', ' ').title()) for s in
                      (*UNRESOLVED_STATUSES, 'completed', 'cancelled', 'expired', 'failed')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_key = models.UUIDField(unique=True)
    request_fingerprint = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name='online_payment_attempts')
    member = models.ForeignKey('memberships.Member', on_delete=models.SET_NULL, null=True, blank=True)
    membership_plan = models.ForeignKey(MembershipPricing, on_delete=models.SET_NULL, null=True)
    stored_member_id = models.CharField(max_length=10)
    customer_name = models.CharField(max_length=150)
    plan_label = models.CharField(max_length=50)
    duration_days = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_centavos = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default='PHP')
    remarks = models.TextField(blank=True)
    mode = models.CharField(max_length=4, choices=[('test', 'Test'), ('live', 'Live')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing', db_index=True)
    payment_intent_id = models.CharField(max_length=100, blank=True, db_index=True)
    payment_method_id = models.CharField(max_length=100, blank=True, db_index=True)
    provider_payment_id = models.CharField(max_length=100, blank=True)
    qr_image = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    test_url = models.URLField(blank=True, max_length=2000)
    message = models.TextField(blank=True)
    review_required = models.BooleanField(default=False)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, null=True, blank=True)
    new_end_date = models.DateField(null=True, blank=True)
    # Persist before each provider mutation: a crash never repeats an unknown charge operation.
    pending_operation = models.CharField(max_length=32, blank=True)
    cancel_reason = models.CharField(max_length=16, blank=True)
    staff_cancelled_at = models.DateTimeField(null=True, blank=True, editable=False)
    work_token = models.UUIDField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(default=timezone.now, db_index=True)
    retry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    objects = OnlinePaymentAttemptQuerySet.as_manager()

    SNAPSHOT_FIELDS = ('request_key', 'request_fingerprint', 'created_by_id', 'stored_member_id',
                       'customer_name', 'plan_label', 'duration_days', 'amount', 'amount_centavos',
                       'currency', 'remarks', 'mode')

    def save(self, *args, **kwargs):
        if not self._state.adding:
            update_fields = kwargs.get('update_fields')
            if update_fields is None or set(update_fields).intersection((*self.SNAPSHOT_FIELDS, 'created_by')):
                original = type(self).objects.filter(pk=self.pk).values(*self.SNAPSHOT_FIELDS).first()
                if original and any(original[field] != getattr(self, field) for field in self.SNAPSHOT_FIELDS):
                    raise ValueError('Checkout snapshots are immutable.')
        super().save(*args, **kwargs)

    @property
    def is_unresolved(self):
        return self.status in UNRESOLVED_STATUSES

    @property
    def blocks_checkout(self):
        return self.is_unresolved and self.staff_cancelled_at is None

    @property
    def is_walkin(self):
        return self.stored_member_id == 'GYMMSGUEST'

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['created_by'], condition=models.Q(status__in=UNRESOLVED_STATUSES, staff_cancelled_at__isnull=True),
                                    name='one_unresolved_qrph_per_staff'),
            models.UniqueConstraint(fields=['mode', 'payment_intent_id'], condition=~models.Q(payment_intent_id=''),
                                    name='unique_qrph_provider_intent'),
            models.UniqueConstraint(fields=['mode', 'provider_payment_id'], condition=~models.Q(provider_payment_id=''),
                                    name='unique_qrph_provider_payment'),
        ]


class PayMongoWebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mode = models.CharField(max_length=4)
    event_id = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20, default='pending', db_index=True)
    work_token = models.UUIDField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(default=timezone.now, db_index=True)
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=250, blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['mode', 'event_id'], name='unique_paymongo_webhook_event')]


class CashPaymentRequest(models.Model):
    request_key = models.UUIDField(primary_key=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fingerprint = models.CharField(max_length=64)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT)
    new_end_date = models.DateField(null=True)
    created_at = models.DateTimeField(default=timezone.now)
