from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Payment

@receiver(pre_save, sender=Payment)
def set_payment_amount(sender, instance, **kwargs):
    """
    Automatically set payment amount to the price of the selected membership plan.
    Only sets if `amount` is not already manually provided.
    """
    if instance.membership_plan and (instance.amount is None):
        instance.amount = instance.membership_plan.price


