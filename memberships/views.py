from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import string
import random
from .models import Member
from .forms import MemberForm


@login_required
def memberships(request):
    """
    Main memberships list view with search, filter, and statistics
    """
    # Get all members
    members = Member.objects.filter(is_deleted=False).select_related('created_by').order_by('-date_created')
    
    # Get today's date for status calculation
    today = timezone.now().date()
    
    # Calculate statistics
    total_members = members.count()
    active_members = 0
    expired_members = 0
    expiring_soon = 0
    
    # Add status to each member and count statistics
    members_with_status = []
    for member in members:
        # Determine status
        if member.is_active and member.end_date >= today:
            days_until_expiry = (member.end_date - today).days
            if days_until_expiry <= 3:
                member.status = 'expiring'
                expiring_soon += 1
            else:
                member.status = 'active'
            active_members += 1
        elif member.end_date < today:
            member.status = 'expired'
            expired_members += 1
        else:
            member.status = 'inactive'
        
        members_with_status.append(member)
    
    # Get filter parameter from URL
    filter_param = request.GET.get('filter', None)
    
    context = {
        'members': members_with_status,
        'total_members': total_members,
        'active_members': active_members,
        'expired_members': expired_members,
        'expiring_soon': expiring_soon,
        'today': today,
        'filter': filter_param,
    }
    
    return render(request, 'memberships/memberships.html', context)


@login_required
def create_member(request):
    """
    Create a new member
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        sex = request.POST.get('sex')
        address = request.POST.get('address')
        emergency_contact = request.POST.get('emergency_contact')
        emergency_phone = request.POST.get('emergency_phone')
        
        # Handle photo upload
        photo = request.FILES.get('member_photo') or request.FILES.get('camera_input')
        
        # Generate unique member ID
        member_id = generate_member_id()
        
        # Set default values for membership details
        # New members are inactive by default until first payment
        today = timezone.now().date()
        
        # Create member
        member = Member.objects.create(
            member_id=member_id,
            name=name,
            email=email if email else None,
            phone_number=phone_number,
            sex=sex,
            address=address,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone,
            start_date=today,  # Placeholder, will be set on first payment
            end_date=today,    # Placeholder, will be set on first payment
            membership_fee=0,  # Placeholder, will be set on first payment
            photo=photo,
            is_active=False,   # Inactive by default until payment
            created_by=request.user
        )
        
        messages.success(request, f'Member {name} added successfully! Process payment to activate membership.')
        return redirect('memberships:memberships')
    
    return redirect('memberships:memberships')


@login_required
def member_detail(request, member_id):
    """
    View and edit member details
    """
    member = get_object_or_404(Member, member_id=member_id, is_deleted=False)
    today = timezone.now().date()
    
    context = {
        'member': member,
        'today': today,
    }
    
    return render(request, 'memberships/member_details.html', context)


@login_required
def update_member(request, member_id):
    """
    Update member information
    """
    member = get_object_or_404(Member, member_id=member_id, is_deleted=False)
    
    if request.method == 'POST':
        # Update fields (excluding read-only fields like name, sex, dates, fee)
        member.phone_number = request.POST.get('phone_number')
        member.email = request.POST.get('email') if request.POST.get('email') else None
        member.address = request.POST.get('address')
        member.emergency_contact = request.POST.get('emergency_contact')
        member.emergency_phone = request.POST.get('emergency_phone')
        
        # Handle photo removal first
        if request.POST.get('remove_photo') == 'true':
            if member.photo:
                member.photo.delete(save=False)  # Delete the actual file
            member.photo = None
        else:
            # Handle photo upload
            photo = request.FILES.get('photo') or request.FILES.get('member_photo_edit') or request.FILES.get('camera_input_edit')
            if photo:
                # Delete old photo if exists
                if member.photo:
                    member.photo.delete(save=False)
                member.photo = photo
        
        member.save()
        
        messages.success(request, f'Member {member.name} updated successfully!')
        return redirect('memberships:member_detail', member_id=member_id)
    
    return redirect('memberships:member_detail', member_id=member_id)


@login_required
def delete_member(request, member_id):
    """
    Delete a member (soft delete)
    """
    if request.method == 'POST':
        member = get_object_or_404(Member, member_id=member_id, is_deleted=False)
        
        # Check if member has active subscription
        today = timezone.now().date()
        if member.is_active and member.end_date >= today:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete member with active subscription'
            })
        
        # Soft delete
        member.is_deleted = True
        member.deleted_at = timezone.now()
        member.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Member {member.name} deleted successfully'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def generate_member_id():
    """
    Generate a unique member ID in format: GYM + 7 random alphanumeric characters
    Example: GYMA1B2C3D
    """
    while True:
        # Generate random alphanumeric string
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        member_id = f'GYM{random_string}'
        
        # Check if it already exists
        if not Member.objects.filter(member_id=member_id).exists():
            return member_id
