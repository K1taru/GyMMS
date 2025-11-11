from django.db import models
from django.utils import timezone
from django.conf import settings

class GymCheckIn(models.Model):
    """Track member check-ins at the gym"""
    member = models.ForeignKey(
        'memberships.Member',
        on_delete=models.CASCADE,
        related_name='check_ins'
    )
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-check_in_time']
        verbose_name = 'Gym Check-In'
        verbose_name_plural = 'Gym Check-Ins'
    
    def __str__(self):
        return f"{self.member.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Calculate duration of gym session"""
        if self.check_out_time:
            return self.check_out_time - self.check_in_time
        return timezone.now() - self.check_in_time


class DashboardStats(models.Model):
    """Store daily dashboard statistics for performance"""
    date = models.DateField(unique=True, default=timezone.now)
    daily_walk_ins = models.IntegerField(default=0)
    total_check_ins = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active_members = models.IntegerField(default=0)
    new_members = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Dashboard Statistics'
        verbose_name_plural = 'Dashboard Statistics'
    
    def __str__(self):
        return f"Stats for {self.date}"
