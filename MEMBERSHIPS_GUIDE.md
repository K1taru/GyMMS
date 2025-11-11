# Memberships Management Guide

## Overview
Complete CRUD (Create, Read, Update, Delete) system for managing gym members with search, filtering, and validation.

## Features Implemented

### 1. **Members List View**
- **Search Bar**: Search by name, member ID, phone, or email
- **Filters**:
  - Status Filter: All, Active, Expired, Expiring Soon
  - Sort: Newest First, Oldest First, Name A-Z, Expiring Soon
- **Statistics Dashboard**:
  - Total Members
  - Active Members (green)
  - Expired Members (red)
  - Expiring Soon (orange - within 7 days)

### 2. **Add New Member (Modal)**
- Modal popup for adding members
- Required fields:
  - Full Name
  - Sex (Male/Female)
  - Phone Number
  - Address
  - Emergency Contact Name
  - Emergency Phone
  - Start Date (defaults to today)
  - End Date (defaults to 30 days from start)
  - Membership Fee
- Optional fields:
  - Email
- **Auto-generated Member ID**: Format `GYM` + 7 random alphanumeric characters

### 3. **Member Actions**
Each member row has action buttons:
- **👁️ View**: View member details (redirects to `/memberships/member/{member_id}/`)
- **✏️ Edit**: Edit member information (redirects to `/memberships/member/{member_id}/edit/`)
- **🗑️ Delete**: Delete member (with restrictions)

### 4. **Delete Protection**
- **Cannot delete** members with active subscriptions
- Alert message: "Cannot delete member with active subscription"
- Only inactive or expired members can be deleted
- Confirmation dialog before deletion

### 5. **Responsive Table**
- Auto-generated member avatars (first letter of name)
- Status badges (Active/Expired/Inactive)
- Member ID display (monospace font)
- Contact information display
- Start/End dates formatted

## URL Structure

```python
# Main memberships page
/memberships/

# Create member (POST only)
/memberships/create/

# Delete member (POST only)
/memberships/member/{member_id}/delete/

# To be implemented:
/memberships/member/{member_id}/         # View details
/memberships/member/{member_id}/edit/    # Edit member
```

## Database Schema

### Member Model Fields
```python
- member_id: CharField (auto-generated, unique)
- name: CharField
- email: EmailField (optional)
- phone_number: CharField
- sex: CharField (Male/Female)
- address: TextField
- emergency_contact: CharField
- emergency_phone: CharField
- start_date: DateField
- end_date: DateField
- membership_fee: DecimalField
- is_active: BooleanField
- created_by: ForeignKey (StaffUser)
- date_created: DateTimeField
```

## JavaScript Functions

### Modal Management
```javascript
openModal(modalId)      // Open modal
closeModal(modalId)     // Close modal and reset form
```

### Member Operations
```javascript
viewMember(memberId)    // View member details
editMember(memberId)    // Edit member
deleteMember(memberId, isActive)  // Delete with validation
```

### Filtering & Search
```javascript
filterMembers()         // Real-time search and filter
sortMembers()          // Sort table by criteria
```

## CSS Classes

### Status Badges
- `.status-badge.active` - Green (active membership)
- `.status-badge.expired` - Red (expired)
- `.status-badge.inactive` - Gray (inactive)

### Action Buttons
- `.btn-view` - Blue (view)
- `.btn-edit` - Green (edit)
- `.btn-delete` - Red (delete, disabled for active members)

### Statistics
- `.stat-value.active` - Green number
- `.stat-value.expired` - Red number
- `.stat-value.expiring` - Orange number

## Usage Flow

### Adding a New Member
1. Click "Add New Member" button
2. Modal opens with form
3. Fill in required fields
4. Start date defaults to today
5. End date auto-calculates (30 days from start)
6. Click "Add Member"
7. Member ID auto-generated
8. Success message displays
9. Table refreshes with new member

### Searching Members
1. Type in search box
2. Results filter in real-time
3. Searches: name, email, member ID, phone

### Filtering by Status
1. Select status from dropdown
2. "Expiring Soon" shows members expiring within 7 days
3. Table updates instantly

### Deleting Members
1. Click delete button
2. If member is active: Alert shows, deletion prevented
3. If member is inactive: Confirmation dialog
4. Click OK to confirm
5. Member removed from table
6. Success message displays

## Security Features

1. **Login Required**: All views require authentication
2. **Delete Validation**: Cannot delete active members
3. **CSRF Protection**: All POST requests include CSRF token
4. **Created By Tracking**: Records which staff created member

## Next Steps (To Implement)

1. **Member Detail View**
   - Full member profile page
   - Payment history
   - Check-in history
   - Edit button

2. **Member Edit View**
   - Pre-filled form with current data
   - Update membership dates
   - Renew membership

3. **Member Check-in Integration**
   - Link to dashboard check-in system
   - Track member visits

4. **Payment Integration**
   - Link to payments module
   - Show payment status

## Responsive Design

- **Desktop**: Full table with all columns
- **Tablet** (< 768px): Scrollable table
- **Mobile** (< 480px): 
  - Stacked filters
  - Compact stats (1 column)
  - Vertical action buttons

## Color Scheme

- **Primary Green**: `#047857` (var(--accent))
- **Active Green**: `#10b981`
- **Expired Red**: `#ef4444`
- **Expiring Orange**: `#f59e0b`
- **View Blue**: `#3b82f6`

## Files Modified/Created

1. `memberships/templates/memberships/memberships.html` - Main template
2. `memberships/static/memberships/css/memberships.css` - Styles (700+ lines)
3. `memberships/static/memberships/js/memberships.js` - JavaScript functionality
4. `memberships/views.py` - Views with CRUD operations
5. `memberships/urls.py` - URL patterns
6. `memberships/models.py` - Added helper properties

## Testing Checklist

- [ ] Add new member with all fields
- [ ] Add member with optional email blank
- [ ] Search by name
- [ ] Search by member ID
- [ ] Search by phone
- [ ] Filter by Active status
- [ ] Filter by Expired status
- [ ] Filter by Expiring Soon
- [ ] Sort by name A-Z
- [ ] Sort by expiring soon
- [ ] Try to delete active member (should fail)
- [ ] Delete inactive member (should succeed)
- [ ] Modal opens/closes properly
- [ ] Form validation works
- [ ] Responsive design on mobile
- [ ] Date auto-calculation works

## Known Limitations

1. Edit and View member pages not yet implemented
2. No pagination (will need it for many members)
3. No export functionality (CSV/PDF)
4. No bulk actions (bulk delete, bulk renew)

## Migration Required

Run migrations to ensure Member model is up to date:
```bash
docker-compose exec web python manage.py makemigrations memberships
docker-compose exec web python manage.py migrate
```
