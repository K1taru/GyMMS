from django.db import models

class Membership_Plan(models.Model):
    MEMBERSHIP_PLANS = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    MEMBER_TYPE = [
        ('regular', 'Regular'),
        ('premium', 'Premium'),
    ]

    name = models.CharField(max_length=50)
    membership_plan = models.CharField(max_length=20, choices=MEMBERSHIP_PLANS)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE, default='regular')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(help_text="Number of days this plan lasts.")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.plan_type.title()} ({self.tier.title()})"
