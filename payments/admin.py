from django.contrib import admin
from .models import PremiumSubscription, AdBoost, Transaction, PricingPlan

@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_type', 'status', 'start_date', 'end_date', 'amount']
    list_filter = ['subscription_type', 'status', 'start_date']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AdBoost)
class AdBoostAdmin(admin.ModelAdmin):
    list_display = ['ad', 'boost_type', 'status', 'start_date', 'end_date', 'amount']
    list_filter = ['boost_type', 'status', 'start_date']
    search_fields = ['ad__title']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_reference', 'user', 'transaction_type', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['transaction_type', 'payment_method', 'status', 'created_at']
    search_fields = ['transaction_reference', 'user__email']
    readonly_fields = ['transaction_reference', 'created_at', 'updated_at']

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_days', 'is_active', 'order']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'price']
