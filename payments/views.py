from django.shortcuts import render

def payments_base(request):
    return render(request, "payments/base.html")
