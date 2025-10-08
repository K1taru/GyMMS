from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from .models import Membership_Plan


def membership_plans_base(request):
    return render(request, "membership_plans/base.html")


@user_passes_test(lambda u: u.is_staff)
def manage_plans(request):
    membership_plans = Membership_Plan.objects.all()
    return render(request, 'plans/manage_plans.html', {'membership_plans': membership_plans})

def available_membership_plans(request):
    membership_plans = Membership_Plan.objects.filter(is_active=True)
    return render(request, 'plans/available_membership_plans.html', {'membership_plans': membership_plans})
