from django.shortcuts import render

def base(request):
    return render(request, "metrics/base.html")
