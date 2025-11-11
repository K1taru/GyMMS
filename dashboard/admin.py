from django.contrib import admin
from .models import GymCheckIn, DashboardStats

@admin.register(GymCheckIn)
class GymCheckInAdmin(admin.ModelAdmin):
    list_display = ('member', 'check_in_time', 'check_out_time', 'date', 'duration')
    list_filter = ('date', 'check_in_time')
    search_fields = ('member__name', 'member__member_id', 'member__email')
    date_hierarchy = 'date'
    ordering = ('-check_in_time',)
    
    def duration(self, obj):
        return obj.duration if obj.check_out_time else "Still in gym"
    duration.short_description = 'Duration'

@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'daily_walk_ins', 'total_check_ins', 'total_revenue', 'active_members', 'new_members')
    list_filter = ('date',)
    date_hierarchy = 'date'
    ordering = ('-date',)
    readonly_fields = ('date', 'daily_walk_ins', 'total_check_ins', 'total_revenue', 'active_members', 'new_members')
