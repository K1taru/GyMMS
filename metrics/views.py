from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def metrics(request):
    return render(request, "metrics/metrics.html")
