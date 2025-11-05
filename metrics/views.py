from django.shortcuts import render

def metrics(request):
    return render(request, "metrics/metrics.html")
