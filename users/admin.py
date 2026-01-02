from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Location, UserVerification, BlockedUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_verified', 'is_premium', 'is_staff', 'joined_date']
    list_filter = ['is_verified', 'is_premium', 'is_staff', 'is_superuser', 'is_active', 'joined_date']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone_number']
    ordering = ['-joined_date']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'location', 'profile_picture', 'bio', 'is_verified', 'is_premium')
        }),
    )

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['city', 'county', 'country']
    list_filter = ['country', 'county']
    search_fields = ['city', 'county', 'country']

@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_verified', 'phone_verified', 'created_at']
    list_filter = ['email_verified', 'phone_verified']
    search_fields = ['user__email']

@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked', 'created_at']
    search_fields = ['blocker__email', 'blocked__email']
