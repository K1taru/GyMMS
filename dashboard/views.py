from django.shortcuts import render

def base(request):
    return render(request, "dashboard/base.html")
