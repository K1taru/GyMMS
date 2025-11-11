# Django Authentication Techniques Guide

## Overview
This guide covers different techniques to restrict access to authenticated users only in Django.

---

## ✅ Applied Techniques in GyMMS

### 1. **`@login_required` Decorator** (Currently Implemented)

**Used For:** Function-Based Views (FBV)

**How It Works:**
- Automatically redirects unauthenticated users to the login page
- Most common and recommended approach for FBVs

**Implementation:**
```python
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, "dashboard/dashboard.html")
```

**Applied To:**
- ✅ `dashboard/views.py` - dashboard view
- ✅ `memberships/views.py` - memberships view
- ✅ `metrics/views.py` - metrics view
- ✅ `payments/views.py` - payments view

**Settings Configuration:**
```python
# config/settings.py
LOGIN_URL = 'core:login'  # Where to redirect if not authenticated
LOGIN_REDIRECT_URL = 'dashboard:dashboard'  # Where to go after login
LOGOUT_REDIRECT_URL = 'core:index'  # Where to go after logout
```

---

## 🔧 Other Available Techniques

### 2. **Manual Check with `request.user.is_authenticated`**

**Use Case:** When you need custom logic or partial page restrictions

```python
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('core:login')
    
    # Your view logic here
    return render(request, "dashboard/dashboard.html")
```

**Pros:**
- Full control over redirect logic
- Can add custom messages

**Cons:**
- More verbose
- Easy to forget

---

### 3. **`LoginRequiredMixin` for Class-Based Views**

**Use Case:** When using Class-Based Views (CBV)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    login_url = '/login/'  # Optional: override default
    redirect_field_name = 'next'  # Optional: customize redirect parameter
```

**Note:** Always put `LoginRequiredMixin` FIRST in the inheritance list!

---

### 4. **`UserPassesTestMixin` - Advanced Permission Check**

**Use Case:** When you need custom permission logic (e.g., only owners)

```python
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView

class OwnerOnlyView(UserPassesTestMixin, TemplateView):
    template_name = 'owner_dashboard.html'
    
    def test_func(self):
        # Only allow users with role='Owner'
        return self.request.user.is_authenticated and self.request.user.role == 'Owner'
    
    def handle_no_permission(self):
        # Custom redirect when test fails
        return redirect('core:login')
```

---

### 5. **`@user_passes_test` Decorator**

**Use Case:** Custom permission check for function-based views

```python
from django.contrib.auth.decorators import user_passes_test

def is_owner(user):
    return user.is_authenticated and user.role == 'Owner'

@user_passes_test(is_owner, login_url='core:login')
def owner_dashboard(request):
    return render(request, 'owner_dashboard.html')
```

---

### 6. **`@permission_required` Decorator**

**Use Case:** Django's built-in permission system

```python
from django.contrib.auth.decorators import permission_required

@permission_required('memberships.add_member', raise_exception=True)
def add_member(request):
    # Only users with 'add_member' permission can access
    return render(request, 'add_member.html')
```

---

### 7. **Middleware-Based Authentication**

**Use Case:** Protect entire sections of your site

```python
# custom_middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_urls = [
            reverse('core:login'),
            reverse('core:index'),
        ]
    
    def __call__(self, request):
        if not request.user.is_authenticated:
            if request.path not in self.public_urls:
                return redirect('core:login')
        
        response = self.get_response(request)
        return response
```

Add to `settings.py`:
```python
MIDDLEWARE = [
    # ... other middleware
    'path.to.custom_middleware.AuthRequiredMiddleware',
]
```

**Warning:** Use carefully - can block static files and admin!

---

### 8. **URL-Level Protection**

**Use Case:** Protect entire URL patterns at once

```python
# urls.py
from django.contrib.auth.decorators import login_required
from django.urls import path

urlpatterns = [
    path('dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    path('metrics/', login_required(MetricsView.as_view()), name='metrics'),
]
```

---

### 9. **Template-Level Checks**

**Use Case:** Show/hide content based on authentication

```django
{% if user.is_authenticated %}
    <p>Welcome, {{ user.username }}!</p>
    <a href="{% url 'dashboard:dashboard' %}">Dashboard</a>
{% else %}
    <p>Please <a href="{% url 'core:login' %}">log in</a></p>
{% endif %}
```

**Check Specific Permissions:**
```django
{% if perms.memberships.add_member %}
    <a href="{% url 'memberships:add' %}">Add Member</a>
{% endif %}
```

---

## 🎯 Recommended Approach for GyMMS

### Current Implementation: ✅ Correct!

**Function-Based Views:**
```python
@login_required
def view_name(request):
    # View logic
```

### Future Enhancements (Optional):

**1. Role-Based Access Control:**
```python
# utils/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        if request.user.role != 'Owner':
            messages.error(request, 'Only owners can access this page.')
            return redirect('dashboard:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

# Usage:
@owner_required
def create_staff(request):
    # Only owners can access this
    pass
```

**2. Staff or Owner Access:**
```python
def staff_or_owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        if request.user.role not in ['Owner', 'Staff']:
            messages.error(request, 'Insufficient permissions.')
            return redirect('dashboard:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## 🔒 Security Best Practices

### 1. **Always Use HTTPS in Production**
```python
# settings.py (Production)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 2. **Set Session Timeout**
```python
# settings.py
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

### 3. **Use Strong Password Validation**
```python
# Already configured in your settings.py
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### 4. **Protect Against Brute Force**
```python
# Install django-axes
# pip install django-axes

# settings.py
INSTALLED_APPS += ['axes']

MIDDLEWARE += ['axes.middleware.AxesMiddleware']

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1  # Lock for 1 hour
```

---

## 🧪 Testing Authentication

### Test Login Required:
```python
# tests.py
from django.test import TestCase, Client
from django.urls import reverse

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:dashboard'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_with_authenticated_user(self):
        # Create and login user
        user = User.objects.create_user(username='test', password='test123')
        self.client.login(username='test', password='test123')
        
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
```

---

## 📋 Summary

| Technique | Use Case | Difficulty | Flexibility |
|-----------|----------|------------|-------------|
| `@login_required` | FBV - Simple auth | ⭐ Easy | ⭐⭐ Low |
| `LoginRequiredMixin` | CBV - Simple auth | ⭐⭐ Easy | ⭐⭐ Low |
| `@user_passes_test` | Custom permissions | ⭐⭐ Medium | ⭐⭐⭐ Medium |
| `UserPassesTestMixin` | CBV Custom perms | ⭐⭐ Medium | ⭐⭐⭐ Medium |
| Middleware | Site-wide protection | ⭐⭐⭐ Hard | ⭐⭐⭐⭐ High |
| Manual checks | Full control | ⭐ Easy | ⭐⭐⭐⭐⭐ Very High |

---

## ✅ Current GyMMS Setup

**Protected Endpoints:**
- ✅ `/dashboard/` - Requires login
- ✅ `/memberships/` - Requires login
- ✅ `/metrics/` - Requires login
- ✅ `/payments/` - Requires login

**Public Endpoints:**
- ✅ `/` (index/login page)
- ✅ `/login/` 
- ✅ `/logout/`

**Redirect Flow:**
1. User tries to access `/dashboard/` without login
2. Django redirects to `/login/?next=/dashboard/`
3. User logs in successfully
4. Django redirects to `/dashboard/` (from `next` parameter)

---

**Last Updated:** November 2025  
**Status:** ✅ Production Ready
