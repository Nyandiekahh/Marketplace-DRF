from django.contrib import admin
from .models import Ad, Image, Favorite, AdView

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'price', 'status', 'premium_type', 'views_count', 'created_at']
    list_filter = ['status', 'premium_type', 'condition', 'category', 'created_at']
    search_fields = ['title', 'description', 'seller__email']
    readonly_fields = ['views_count', 'contact_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    actions = ['mark_as_active', 'mark_as_expired', 'mark_as_sold']
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = "Mark selected ads as Active"
    
    def mark_as_expired(self, request, queryset):
        queryset.update(status='expired')
    mark_as_expired.short_description = "Mark selected ads as Expired"
    
    def mark_as_sold(self, request, queryset):
        queryset.update(status='sold')
    mark_as_sold.short_description = "Mark selected ads as Sold"

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['ad', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['ad__title']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'ad', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'ad__title']

@admin.register(AdView)
class AdViewAdmin(admin.ModelAdmin):
    list_display = ['ad', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['ad__title', 'user__email', 'ip_address']
