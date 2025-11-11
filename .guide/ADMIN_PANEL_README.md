# Admin Panel Documentation

## Overview
The Admin Panel is accessible only to users with the **Owner** role. It provides comprehensive staff and pricing management functionality.

## Access
- **URL**: `/users/admin/`
- **Navigation**: Click the "Admin" button in the profile dropdown menu (visible only to Owners)
- **Authentication**: Requires Owner role, otherwise returns 403 Forbidden

## Features

### 1. Staff Management
Manage gym staff members with full CRUD operations.

#### View Staff
- Lists all active staff members in a table
- Displays: Name, Email, Phone, Role, Status, Actions

#### Add Staff
- Click the "Add Staff" button
- Fill in the form:
  - Name (required)
  - Email (required, must be unique)
  - Phone Number (optional)
  - Role (Owner or Staff)
  - Password (required)
  - Confirm Password (required)
- Submits via AJAX, no page reload

#### Edit Staff
- Click the edit icon (pencil) on any staff row
- Modifies existing staff details
- Password field is optional (only fill if changing password)
- Email uniqueness is validated
- Submits via AJAX

#### Delete Staff
- Click the delete icon (trash) on any staff row
- Confirmation dialog appears
- Performs soft delete (sets `is_active = False`)
- Submits via AJAX

### 2. Pricing Management
Manage membership pricing plans.

#### View Pricing Plans
- Displays all active pricing plans in a card grid
- Shows: Plan name, Price (₱), Duration (days)

#### Add Pricing Plan
- Click the "Add Pricing Plan" button
- Fill in the form:
  - Plan Name (required, must be unique)
  - Price (required, decimal)
  - Duration in Days (required, integer)
- Submits via AJAX

#### Edit Pricing Plan
- Click the "Edit" button on any pricing card
- Modifies existing plan details
- Plan name uniqueness is validated
- Submits via AJAX

#### Delete Pricing Plan
- Click the "Delete" button on any pricing card
- Confirmation dialog appears
- Performs soft delete (sets `is_active = False`)
- Submits via AJAX

## Technical Details

### Frontend Files
- **Template**: `users/templates/users/admin.html`
- **CSS**: `users/static/users/css/admin.css`
- **JavaScript**: `users/static/users/js/admin.js`

### Backend Views (users/views.py)
All views require Owner role authentication:

1. `admin_panel(request)` - Main panel view
2. `create_staff(request)` - POST endpoint for creating staff
3. `get_staff(request, staff_id)` - GET endpoint for staff details
4. `update_staff(request)` - POST endpoint for updating staff
5. `delete_staff(request, staff_id)` - POST endpoint for deleting staff
6. `create_pricing(request)` - POST endpoint for creating pricing plan
7. `get_pricing(request, pricing_id)` - GET endpoint for pricing details
8. `update_pricing(request)` - POST endpoint for updating pricing plan
9. `delete_pricing(request, pricing_id)` - POST endpoint for deleting pricing plan

### URL Routes (users/urls.py)
```python
/users/admin/                          # Main admin panel
/users/admin/staff/create/             # Create staff (POST)
/users/admin/staff/<id>/               # Get staff details (GET)
/users/admin/staff/update/             # Update staff (POST)
/users/admin/staff/delete/<id>/        # Delete staff (POST)
/users/admin/pricing/create/           # Create pricing (POST)
/users/admin/pricing/<id>/             # Get pricing details (GET)
/users/admin/pricing/update/           # Update pricing (POST)
/users/admin/pricing/delete/<id>/      # Delete pricing (POST)
```

### Database Models

#### StaffUser (existing)
- Extends Django's AbstractUser
- Fields: username, email, phone_number, role, created_by
- Role choices: Owner, Staff

#### MembershipPlan (new)
- Fields:
  - `name` - CharField (100, unique)
  - `price` - DecimalField (10, 2)
  - `duration_days` - IntegerField
  - `created_at` - DateTimeField (auto_now_add)
  - `updated_at` - DateTimeField (auto_now)
  - `is_active` - BooleanField (default=True)

### Security Features
- `@login_required` decorator on all views
- Role-based access control (Owner only)
- CSRF token protection on all POST requests
- Email uniqueness validation
- Password hashing for staff accounts
- Soft delete (preserves data, sets is_active=False)

### AJAX Implementation
All CRUD operations use AJAX for seamless UX:
- No page reloads on form submissions
- JSON response format: `{success: true/false, message: "..."}`
- Error handling with user-friendly messages
- Modal-based forms with proper validation

### UI Features
- **Tab Navigation**: Switch between Staff and Pricing management
- **Responsive Design**: Works on desktop and mobile
- **Modal System**: Reusable modals for forms and confirmations
- **Animations**: Smooth fade-in and slide-up effects
- **Color-Coded Badges**: 
  - Roles: Owner (blue), Staff (green)
  - Status: Active (green), Inactive (gray)
- **Hover Effects**: Interactive cards and buttons
- **ESC Key Support**: Close modals with ESC key
- **Outside Click**: Close modals by clicking backdrop

## Usage Examples

### Creating a Staff Member
1. Navigate to Admin panel
2. Ensure "Staff Management" tab is active
3. Click "Add Staff" button
4. Fill in form (ensure passwords match)
5. Click "Create Staff"
6. Success message appears, page reloads with new staff

### Editing Pricing Plan
1. Navigate to Admin panel
2. Click "Pricing Management" tab
3. Find the plan to edit
4. Click "Edit" button
5. Modify fields in modal
6. Click "Update Plan"
7. Success message appears, page reloads

### Deleting Staff
1. Find staff member in table
2. Click trash icon in Actions column
3. Confirm deletion in dialog
4. Success message appears, staff removed from list

## Migration Commands
```bash
# Create migration for MembershipPlan model
docker-compose exec web python manage.py makemigrations users

# Apply migration
docker-compose exec web python manage.py migrate users
```

## Testing Checklist
- [ ] Owner can access admin panel
- [ ] Non-Owner users get 403 Forbidden
- [ ] Staff creation works with all validations
- [ ] Staff editing works (password optional)
- [ ] Staff deletion soft-deletes record
- [ ] Pricing creation validates uniqueness
- [ ] Pricing editing works correctly
- [ ] Pricing deletion soft-deletes record
- [ ] AJAX requests return proper JSON
- [ ] Modals open/close correctly
- [ ] Tab switching works
- [ ] Form validation shows errors
- [ ] Success messages display properly
- [ ] ESC key closes modals
- [ ] Responsive design on mobile

## Future Enhancements
- [ ] Bulk staff import via CSV
- [ ] Staff activity logs
- [ ] Advanced pricing features (discounts, promos)
- [ ] Email notifications for new staff
- [ ] Staff performance metrics
- [ ] Pricing plan analytics
- [ ] Export staff list to PDF/Excel
