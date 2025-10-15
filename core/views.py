from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

def index(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard:base")
    return render(request, "core/index.html")

def login(request):
    return render(request, "core/login.html")

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Basic validation
        if password != password2:
            return render(request, 'core/register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'core/register.html', {'error': 'Username already exists'})

        if User.objects.filter(email=email).exists():
            return render(request, 'core/register.html', {'error': 'Email already exists'})

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # TODO: Save phone number to a profile model if needed
        messages.success(request, 'Account created successfully. Please login.')
        return redirect('core:login')

    return render(request, 'core/register.html')
