from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal


class PaymentSummary(models.Model):
    month = models.DateField(unique=True, help_text='First day of the month')
    total_income = models.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = models.PositiveIntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-month']
        verbose_name = 'Payment Summary'
        verbose_name_plural = 'Payment Summaries'
        indexes = [
            models.Index(fields=['month']),
        ]
    
    def __str__(self):
        return f"Summary for {self.month.strftime('%B %Y')}"


class ActiveMemberSnapshot(models.Model):
    """
    Daily snapshot of active member counts for historical tracking
    Enables accurate time-series analysis of member activity
    """
    date = models.DateField(unique=True, default=timezone.now, db_index=True)
    active_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of members with active memberships on this date'
    )
    total_members = models.PositiveIntegerField(
        default=0,
        help_text='Total number of non-deleted members on this date'
    )
    new_members_today = models.PositiveIntegerField(
        default=0,
        help_text='New members registered on this date'
    )
    expired_today = models.PositiveIntegerField(
        default=0,
        help_text='Memberships that expired on this date'
    )
    total_revenue_today = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Total revenue collected on this date'
    )
    check_ins_today = models.PositiveIntegerField(
        default=0,
        help_text='Total check-ins on this date'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Active Member Snapshot'
        verbose_name_plural = 'Active Member Snapshots'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"{self.date}: {self.active_count} active members"
    
    @classmethod
    def create_snapshot(cls, target_date=None):
        """
        Create or update snapshot for a specific date
        If target_date is None, uses today
        """
        from memberships.models import Member
        from payments.models import Payment
        from dashboard.models import GymCheckIn
        
        if target_date is None:
            target_date = timezone.now().date()
        
        # Count active members (membership valid on this date)
        active_count = Member.objects.filter(
            is_active=True,
            is_deleted=False,
            start_date__lte=target_date,
            end_date__gte=target_date
        ).count()
        
        # Total non-deleted members
        total_members = Member.objects.filter(
            is_deleted=False,
            date_created__date__lte=target_date
        ).count()
        
        # New members created on this date
        new_members_today = Member.objects.filter(
            is_deleted=False,
            date_created__date=target_date
        ).count()
        
        # Memberships that expired on this date
        expired_today = Member.objects.filter(
            is_deleted=False,
            end_date=target_date
        ).count()
        
        # Revenue collected on this date
        total_revenue_today = Payment.objects.filter(
            payment_date__date=target_date,
            status='Completed'
        ).aggregate(total=Coalesce(models.Sum('amount'), Decimal('0.00')))['total']
        
        # Check-ins on this date
        check_ins_today = GymCheckIn.objects.filter(
            date=target_date
        ).count()
        
        # Create or update snapshot
        snapshot, created = cls.objects.update_or_create(
            date=target_date,
            defaults={
                'active_count': active_count,
                'total_members': total_members,
                'new_members_today': new_members_today,
                'expired_today': expired_today,
                'total_revenue_today': total_revenue_today,
                'check_ins_today': check_ins_today,
            }
        )
        
        return snapshot
