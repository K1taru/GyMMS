"""
Check-in/Check-out Helper Views
Add these to your dashboard/views.py or create a separate file
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import GymCheckIn
from memberships.models import Member

@login_required
def member_check_in(request, member_id):
    """
    Check in a member to the gym
    """
    member = get_object_or_404(Member, id=member_id)
    
    # Check if member is already checked in today
    today = timezone.now().date()
    existing_check_in = GymCheckIn.objects.filter(
        member=member,
        date=today,
        check_out_time__isnull=True
    ).first()
    
    if existing_check_in:
        messages.warning(request, f'{member.get_full_name()} is already checked in.')
    else:
        # Create new check-in
        GymCheckIn.objects.create(
            member=member,
            check_in_time=timezone.now(),
            date=today
        )
        messages.success(request, f'{member.get_full_name()} checked in successfully!')
    
    return redirect('dashboard:dashboard')


@login_required
def member_check_out(request, check_in_id):
    """
    Check out a member from the gym
    """
    check_in = get_object_or_404(GymCheckIn, id=check_in_id)
    
    if check_in.check_out_time:
        messages.warning(request, f'{check_in.member.get_full_name()} already checked out.')
    else:
        check_in.check_out_time = timezone.now()
        check_in.save()
        messages.success(request, f'{check_in.member.get_full_name()} checked out successfully!')
    
    return redirect('dashboard:dashboard')


@login_required
def quick_check_in(request):
    """
    Quick check-in page with member search
    """
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        if member_id:
            return member_check_in(request, member_id)
    
    # Get all active members for the dropdown
    active_members = Member.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'active_members': active_members,
    }
    
    return render(request, 'dashboard/quick_check_in.html', context)


@login_required
def search_member_ajax(request):
    """
    AJAX endpoint for searching members by name or email
    Returns JSON with matching members
    """
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'members': []})
    
    members = Member.objects.filter(
        is_active=True
    ).filter(
        first_name__icontains=query
    ) | Member.objects.filter(
        is_active=True
    ).filter(
        last_name__icontains=query
    ) | Member.objects.filter(
        is_active=True
    ).filter(
        email__icontains=query
    )
    
    members = members.distinct()[:10]
    
    members_data = [{
        'id': m.id,
        'name': m.get_full_name(),
        'email': m.email,
        'membership_type': m.membership_type,
        'is_checked_in': GymCheckIn.objects.filter(
            member=m,
            date=timezone.now().date(),
            check_out_time__isnull=True
        ).exists()
    } for m in members]
    
    return JsonResponse({'members': members_data})


# Add these URL patterns to dashboard/urls.py:
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('check-in/<int:member_id>/', views.member_check_in, name='member_check_in'),
    path('check-out/<int:check_in_id>/', views.member_check_out, name='member_check_out'),
    path('quick-check-in/', views.quick_check_in, name='quick_check_in'),
    path('api/search-member/', views.search_member_ajax, name='search_member_ajax'),
]
"""
