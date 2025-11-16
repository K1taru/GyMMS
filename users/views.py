import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.conf import settings
from django.template.loader import render_to_string
from .models import StaffUser
from payments.models import MembershipPricing

@login_required
def profile(request):
    """User profile view - allows users to view and edit their own profile"""
    user = request.user
    
    if request.method == 'POST':
        data = request.POST
        files = request.FILES
        response = {'success': False}

        # Update fields except username
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone_number = data.get('phone_number', user.phone_number)

        # Handle image upload
        if 'profile_image' in files:
            image = files['profile_image']
            ext = os.path.splitext(image.name)[1]
            filename = f"{user.username}{ext}"
            save_path = os.path.join('staff_photos', filename)
            full_path = os.path.join(settings.MEDIA_ROOT, save_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Remove old image if exists and different
            if user.profile_image and user.profile_image.name != save_path:
                try:
                    old_path = os.path.join(settings.MEDIA_ROOT, user.profile_image.name)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception:
                    pass
            
            with open(full_path, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            user.profile_image = save_path

        # Handle password change
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        if password:
            if password != password_confirm:
                return JsonResponse({'success': False, 'message': 'Passwords do not match'})
            if len(password) < 6:
                return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters'})
            user.set_password(password)
            update_session_auth_hash(request, user)

        user.save()
        response['success'] = True
        response['message'] = 'Profile updated successfully.'
        if user.profile_image:
            response['profile_image_url'] = settings.MEDIA_URL + user.profile_image.name
        return JsonResponse(response)

    # GET: Render profile page
    return render(request, 'users/profile.html', {'user': user})


@login_required
@require_http_methods(["POST"])
def delete_profile_photo(request):
    """Delete the user's profile photo from disk and clear the profile_image field"""
    user = request.user
    if user.profile_image:
        try:
            photo_path = user.profile_image.path if hasattr(user.profile_image, 'path') else os.path.join(settings.MEDIA_ROOT, str(user.profile_image))
            if os.path.exists(photo_path):
                os.remove(photo_path)
            user.profile_image = ''
            user.save()
            return JsonResponse({'success': True, 'message': 'Profile photo deleted.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'No profile photo to delete.'})


@login_required
def staff_management(request):
    if request.user.role != 'Owner':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    staff_members = StaffUser.objects.filter(role='Staff', is_active=True).order_by('-date_joined')
    return render(request, 'users/staff_management.html', {'staff_members': staff_members})

@login_required
def membership_pricing(request):
    if request.user.role != 'Owner':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    pricing_plans = MembershipPricing.objects.filter(is_active=True).order_by('duration_days')
    return render(request, 'users/membership_pricing.html', {'pricing_plans': pricing_plans})

def base(request):
    return render(request, "users/base.html")


@login_required
def admin_panel(request):
    """Admin panel view - only accessible by Owner"""
    if request.user.role != 'Owner':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    staff_members = StaffUser.objects.filter(role='Staff', is_active=True).order_by('-date_joined')
    pricing_plans = MembershipPricing.objects.filter(is_active=True).order_by('duration_days')
    context = {
        'staff_members': staff_members,
        'pricing_plans': pricing_plans,
    }

    # AJAX partial for pricing grid refresh
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('pricing_only') == '1':
        html = render_to_string('users/_pricing_grid.html', {'pricing_plans': pricing_plans})
        return JsonResponse({'success': True, 'html': html})

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
        if not username:
            return JsonResponse({'success': False, 'message': 'Username is required'})
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        if not password:
            return JsonResponse({'success': False, 'message': 'Password is required'})
        
        # Check if username already exists (only check active users)
        if StaffUser.objects.filter(username=username, is_active=True).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'})
        
        # Validate password length
        if len(password) < 6:
            return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long'})
        
        # Create staff user
        with transaction.atomic():
            staff = StaffUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                name=name or '',
                phone_number=phone_number or '',
                role=role,
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Staff member {name or username} created successfully!'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["GET"])
def get_staff(request, staff_id):
    """Get staff member details"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        staff = get_object_or_404(StaffUser, id=staff_id, is_active=True)
        
        # Ensure we're only getting staff members, not owners
        if staff.role != 'Staff':
            return JsonResponse({'success': False, 'message': 'Invalid staff member'})
        
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
    """Update staff member - Owner can update name, email, phone, and password"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        staff_id = request.POST.get('staff_id')
        if not staff_id:
            return JsonResponse({'success': False, 'message': 'Staff ID is required'})
            
        staff = get_object_or_404(StaffUser, id=staff_id, is_active=True)
        
        # Ensure we're only updating staff members, not owners
        if staff.role != 'Staff':
            return JsonResponse({'success': False, 'message': 'Cannot update this user'})
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        # Owner can update name, email, phone number, and password
        # Username and role cannot be changed
        
        if name is not None:
            staff.name = name
        
        if email:
            staff.email = email
        
        if phone_number is not None:
            staff.phone_number = phone_number
        
        # Update password if provided
        if password:
            if len(password) < 6:
                return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long'})
            staff.set_password(password)
        
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Staff member updated successfully!'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_staff(request, staff_id):
    """Delete staff member (hard delete)"""
    if request.user.role != 'Owner':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        staff = get_object_or_404(StaffUser, id=staff_id, is_active=True)
        
        # Ensure we're only deleting staff members, not owners
        if staff.role != 'Staff':
            return JsonResponse({'success': False, 'message': 'Cannot delete this user'})
        
        # Prevent deleting yourself
        if staff.id == request.user.id:
            return JsonResponse({'success': False, 'message': 'Cannot delete your own account'})
        
        # Hard delete - permanently remove from database
        staff.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Staff member deleted successfully!'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
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
