from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import StaffUser
from payments.models import MembershipPricing

def base(request):
    return render(request, "users/base.html")


@login_required
def admin_panel(request):
    """Admin panel view - only accessible by Owner"""
    if request.user.role != 'Owner':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get all staff members (excluding the current owner)
    staff_members = StaffUser.objects.filter(role='Staff', is_active=True).order_by('-date_joined')
    
    # Get all pricing plans
    pricing_plans = MembershipPricing.objects.filter(is_active=True).order_by('duration_days')
    
    context = {
        'staff_members': staff_members,
        'pricing_plans': pricing_plans,
    }
    
    return render(request, 'users/admin.html', context)


@login_required
@require_http_methods(["POST"])
def create_staff(request):
    """Create a new staff member"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        role = request.POST.get('role', 'Staff')
        password = request.POST.get('password')
        
        # Validation
        if not all([username, name, email, password]):
            return JsonResponse({'success': False, 'message': 'Username, name, email, and password are required'})
        
        # Check if email already exists
        if StaffUser.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'})
        
        # Check if username already exists
        if StaffUser.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'})
        
        # Create staff user
        with transaction.atomic():
            staff = StaffUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                name=name,
                phone_number=phone_number,
                role=role,
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Staff member {name} created successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["GET"])
def get_staff(request, staff_id):
    """Get staff member details"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        staff = get_object_or_404(StaffUser, id=staff_id, role='Staff')
        
        return JsonResponse({
            'success': True,
            'staff': {
                'id': staff.id,
                'username': staff.username,
                'name': staff.name or '',
                'email': staff.email,
                'phone_number': staff.phone_number or '',
                'role': staff.role,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_staff(request):
    """Update staff member - Owner can only update name, email, and phone"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        staff_id = request.POST.get('staff_id')
        staff = get_object_or_404(StaffUser, id=staff_id, role='Staff')
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        
        # Owner can only update name, email, and phone number
        # Username and password cannot be changed by owner
        
        if name is not None:
            staff.name = name
        
        if email and email != staff.email:
            if StaffUser.objects.filter(email=email).exclude(id=staff_id).exists():
                return JsonResponse({'success': False, 'message': 'Email already exists'})
            staff.email = email
        
        if phone_number is not None:
            staff.phone_number = phone_number
        
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Staff member updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_staff(request, staff_id):
    """Delete staff member (soft delete)"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        staff = get_object_or_404(StaffUser, id=staff_id, role='Staff')
        staff.is_active = False
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Staff member deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def create_pricing(request):
    """Create a new pricing plan"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        duration_label = request.POST.get('duration_label')
        price = request.POST.get('price')
        duration_days = request.POST.get('duration_days')
        
        # Validation
        if not all([duration_label, price, duration_days]):
            return JsonResponse({'success': False, 'message': 'All fields are required'})
        
        # Create pricing plan (allow duplicate duration_days)
        plan = MembershipPricing.objects.create(
            duration_label=duration_label,
            price=price,
            duration_days=duration_days
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Pricing plan "{duration_label}" created successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["GET"])
def get_pricing(request, pricing_id):
    """Get pricing plan details"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        plan = get_object_or_404(MembershipPricing, id=pricing_id)
        
        return JsonResponse({
            'success': True,
            'plan': {
                'id': plan.id,
                'duration_label': plan.duration_label,
                'price': str(plan.price),
                'duration_days': plan.duration_days,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_pricing(request):
    """Update pricing plan"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        pricing_id = request.POST.get('pricing_id')
        plan = get_object_or_404(MembershipPricing, id=pricing_id)
        
        duration_label = request.POST.get('duration_label')
        price = request.POST.get('price')
        duration_days = request.POST.get('duration_days')
        
        # Update fields (allow duplicate duration_days)
        if duration_days:
            plan.duration_days = duration_days
        
        if duration_label:
            plan.duration_label = duration_label
        
        if price:
            plan.price = price
        
        plan.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Pricing plan updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_pricing(request, pricing_id):
    """Delete pricing plan (soft delete)"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        plan = get_object_or_404(MembershipPricing, id=pricing_id)
        plan.is_active = False
        plan.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Pricing plan deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
