from django.contrib import admin
from .models import Member, MembershipConfig


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """
    Admin interface for Member model
    """
    list_display = [
        'member_id',
        'name',
        'phone_number',
        'email',
        'start_date',
        'end_date',
        'is_active',
        'is_membership_active',
        'date_created'
    ]
    list_filter = [
        'is_active',
        'sex',
        'start_date',
        'end_date',
        'date_created'
    ]
    search_fields = [
        'member_id',
        'name',
        'email',
        'phone_number'
    ]
    readonly_fields = [
        'member_id',
        'date_created',
        'created_by'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('member_id', 'name', 'email', 'phone_number', 'sex', 'address', 'photo')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Membership Details', {
            'fields': ('start_date', 'end_date', 'membership_fee', 'is_active')
        }),
        ('Tracking', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MembershipConfig)
class MembershipConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for MembershipConfig
    """
    list_display = ['membership_fee', 'last_modified']
    
    def has_add_permission(self, request):
        # Only allow one config instance
        return not MembershipConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False
