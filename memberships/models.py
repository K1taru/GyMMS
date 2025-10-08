from django.db import models
from django.conf import settings
from django.utils import timezone

class Member(models.Model):    
    member = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='member_profile', 
        limit_choices_to={'role': 'member'}
    )
    
     # Membership details
    membership_plan = models.ForeignKey(
        'membership_plans.Membership_Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_members'
    )
    last_membership_plan = models.ForeignKey(
        'membership_plans.Membership_Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_members'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
        
    #Check if the membership is still valid.
    def is_membership_active(self):
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
    
    # Update membership period and record last subscription.
    def renew_membership_plan(self, new_membership_plan):
        if not new_membership_plan:
            return

        # Record previous plan
        self.last_membership_plan = self.membership_plan
        self.membership_plan = new_membership_plan
        self.start_date = timezone.now().date()

        # Extend end_date based on plan duration
        self.end_date = self.start_date + timezone.timedelta(days=new_membership_plan.duration_days)
        self.is_active = True
        self.save()
        
    def __str__(self):
        return f"Membership for {self.member.username}"
