from django.contrib import admin
from .models import Membership_Plan

@admin.register(Membership_Plan)
class Membership_Plan_Admin(admin.ModelAdmin):
    list_display = ('name', 'membership_plan', 'membership_type', 'price', 'duration_days', 'is_active')
    list_filter = ('membership_plan', 'membership_type', 'is_active')
    search_fields = ('name',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_staff or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff or request.user.is_superuser
