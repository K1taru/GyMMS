from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from users.models import StaffUser


def index(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard:dashboard")
    return render(request, "core/index.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("dashboard:dashboard")  # Redirect after successful login
        else:
            return render(request, "core/index.html", {"error": "Invalid username or password"})

    return render(request, "core/index.html")


@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect("core:index")
