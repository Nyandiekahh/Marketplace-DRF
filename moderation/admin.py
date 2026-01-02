from django.contrib import admin
from .models import Report, Review

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'report_type', 'reason', 'status', 'created_at', 'resolved_by']
    list_filter = ['report_type', 'reason', 'status', 'created_at']
    search_fields = ['reporter__email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['mark_as_resolved', 'mark_as_dismissed']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_by=request.user)
    mark_as_resolved.short_description = "Mark selected reports as Resolved"
    
    def mark_as_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
    mark_as_dismissed.short_description = "Mark selected reports as Dismissed"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'reviewed_user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__email', 'reviewed_user__email', 'comment']
