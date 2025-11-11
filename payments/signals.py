from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Payment
from memberships.models import Member

@receiver(pre_save, sender=Payment)
def set_payment_amount(sender, instance, **kwargs):
    """
    Automatically set payment amount to the price of the selected membership plan.
    Only sets if `amount` is not already manually provided.
    """
    if instance.membership_plan and (instance.amount is None):
        instance.amount = instance.membership_plan.price

@receiver(post_save, sender=Payment)
def update_membership(sender, instance, created, **kwargs):
    if created:
        # Make sure the user has a member profile
        try:
            member_profile = instance.member.member_profile
        except Member.DoesNotExist:
            return  # No member profile, nothing to do

        # Determine the membership plan from the plan linked to the payment
        new_membership_plan = instance.membership_plan.membership_plan if instance.membership_plan else 'monthly'

        # Renew membership
        member_profile.renew_membership(new_membership_plan)

