from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payments(request):
    return render(request, "payments/payments.html")
