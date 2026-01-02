"""
URL configuration for payments app.
"""

from django.urls import path
from .views import (
    PricingPlanListView,
    MySubscriptionsView,
    PurchaseSubscriptionView,
    MyAdBoostsView,
    PurchaseAdBoostView,
    MyTransactionsView,
    TransactionDetailView,
    PaymentCallbackView,
    CancelSubscriptionView,
    ActiveSubscriptionView,
)

app_name = 'payments'

urlpatterns = [
    # Pricing plans
    path('plans/', PricingPlanListView.as_view(), name='pricing_plans'),
    
    # Subscriptions
    path('subscriptions/', MySubscriptionsView.as_view(), name='my_subscriptions'),
    path('subscriptions/active/', ActiveSubscriptionView.as_view(), name='active_subscription'),
    path('subscriptions/purchase/', PurchaseSubscriptionView.as_view(), name='purchase_subscription'),
    path('subscriptions/<int:pk>/cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    
    # Ad Boosts
    path('boosts/', MyAdBoostsView.as_view(), name='my_boosts'),
    path('boosts/purchase/', PurchaseAdBoostView.as_view(), name='purchase_boost'),
    
    # Transactions
    path('transactions/', MyTransactionsView.as_view(), name='my_transactions'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    
    # Payment callbacks
    path('callback/', PaymentCallbackView.as_view(), name='payment_callback'),
]