from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def index(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard:base")
    return render(request, "core/index.html")
