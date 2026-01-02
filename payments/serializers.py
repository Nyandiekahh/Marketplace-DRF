"""
Serializers for the payments app.
"""

from rest_framework import serializers
from .models import PremiumSubscription, AdBoost, Transaction, PricingPlan


class PremiumSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for premium subscriptions."""
    
    is_active = serializers.BooleanField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = PremiumSubscription
        fields = [
            'id', 'user', 'user_email', 'subscription_type',
            'status', 'amount', 'currency', 'start_date',
            'end_date', 'auto_renew', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'start_date', 'end_date',
            'created_at', 'updated_at'
        ]


class SubscriptionPurchaseSerializer(serializers.Serializer):
    """Serializer for purchasing a subscription."""
    
    subscription_type = serializers.ChoiceField(
        choices=PremiumSubscription.SUBSCRIPTION_TYPE_CHOICES
    )
    duration_days = serializers.IntegerField(
        min_value=1,
        max_value=365,
        default=30
    )
    payment_method = serializers.ChoiceField(
        choices=Transaction.PAYMENT_METHOD_CHOICES
    )
    auto_renew = serializers.BooleanField(default=False)


class AdBoostSerializer(serializers.ModelSerializer):
    """Serializer for ad boosts."""
    
    is_active = serializers.BooleanField(read_only=True)
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    
    class Meta:
        model = AdBoost
        fields = [
            'id', 'ad', 'ad_title', 'boost_type', 'status',
            'amount', 'currency', 'start_date', 'end_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'start_date', 'end_date',
            'created_at', 'updated_at'
        ]


class AdBoostPurchaseSerializer(serializers.Serializer):
    """Serializer for purchasing an ad boost."""
    
    ad_id = serializers.IntegerField()
    boost_type = serializers.ChoiceField(
        choices=AdBoost.BOOST_TYPE_CHOICES
    )
    duration_days = serializers.IntegerField(
        min_value=1,
        max_value=30,
        default=7
    )
    payment_method = serializers.ChoiceField(
        choices=Transaction.PAYMENT_METHOD_CHOICES
    )
    
    def validate_ad_id(self, value):
        """Validate that ad exists and belongs to user."""
        from ads.models import Ad
        request = self.context['request']
        
        try:
            ad = Ad.objects.get(id=value, seller=request.user)
        except Ad.DoesNotExist:
            raise serializers.ValidationError(
                "Ad not found or you don't have permission to boost it."
            )
        
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_email', 'transaction_type',
            'subscription', 'ad_boost', 'amount', 'currency',
            'payment_method', 'status', 'transaction_reference',
            'payment_provider_reference', 'metadata', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'transaction_reference', 'status',
            'created_at', 'updated_at'
        ]


class PricingPlanSerializer(serializers.ModelSerializer):
    """Serializer for pricing plans."""
    
    class Meta:
        model = PricingPlan
        fields = [
            'id', 'name', 'plan_type', 'description',
            'price', 'currency', 'duration_days',
            'features', 'is_active', 'order'
        ]


class PaymentInitiationSerializer(serializers.Serializer):
    """Serializer for initiating a payment."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(
        choices=Transaction.PAYMENT_METHOD_CHOICES
    )
    phone_number = serializers.CharField(
        required=False,
        help_text='Required for M-Pesa payments'
    )


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for payment callback data."""
    
    transaction_reference = serializers.CharField()
    payment_provider_reference = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=['completed', 'failed']
    )
    metadata = serializers.JSONField(required=False)