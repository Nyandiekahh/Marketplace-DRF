"""
Views for the payments app.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import PremiumSubscription, AdBoost, Transaction, PricingPlan
from .serializers import (
    PremiumSubscriptionSerializer,
    SubscriptionPurchaseSerializer,
    AdBoostSerializer,
    AdBoostPurchaseSerializer,
    TransactionSerializer,
    PricingPlanSerializer,
    PaymentInitiationSerializer,
    PaymentCallbackSerializer
)
from ads.models import Ad


class PricingPlanListView(generics.ListAPIView):
    """
    API endpoint to list pricing plans.
    GET: List all active pricing plans.
    """
    
    serializer_class = PricingPlanSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return active pricing plans."""
        queryset = PricingPlan.objects.filter(is_active=True)
        
        # Filter by plan type if specified
        plan_type = self.request.query_params.get('plan_type')
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        
        return queryset


class MySubscriptionsView(generics.ListAPIView):
    """
    API endpoint to list user's subscriptions.
    GET: List authenticated user's subscriptions.
    """
    
    serializer_class = PremiumSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's subscriptions."""
        return PremiumSubscription.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class PurchaseSubscriptionView(APIView):
    """
    API endpoint to purchase a subscription.
    POST: Initiate subscription purchase.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Initiate subscription purchase."""
        serializer = SubscriptionPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        subscription_type = serializer.validated_data['subscription_type']
        duration_days = serializer.validated_data['duration_days']
        payment_method = serializer.validated_data['payment_method']
        auto_renew = serializer.validated_data['auto_renew']
        
        # Calculate amount based on subscription type and duration
        # This is a placeholder - integrate with actual pricing logic
        pricing = {
            'basic': 0,
            'premium': 999,
            'pro': 2499,
            'enterprise': 4999
        }
        amount = pricing.get(subscription_type, 0) * (duration_days / 30)
        
        # Create subscription
        subscription = PremiumSubscription.objects.create(
            user=request.user,
            subscription_type=subscription_type,
            amount=amount,
            auto_renew=auto_renew
        )
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='subscription',
            subscription=subscription,
            amount=amount,
            payment_method=payment_method,
            status='pending'
        )
        
        # Here you would integrate with payment gateway
        # For now, we'll return the transaction details
        
        return Response({
            'message': 'Subscription purchase initiated.',
            'subscription': PremiumSubscriptionSerializer(subscription).data,
            'transaction': TransactionSerializer(transaction).data,
            'payment_instructions': self._get_payment_instructions(
                payment_method,
                transaction
            )
        }, status=status.HTTP_201_CREATED)
    
    def _get_payment_instructions(self, payment_method, transaction):
        """Get payment instructions based on method."""
        if payment_method == 'mpesa':
            return {
                'method': 'M-Pesa',
                'instructions': 'Please complete payment via M-Pesa.',
                'transaction_reference': transaction.transaction_reference
            }
        elif payment_method == 'card':
            return {
                'method': 'Card',
                'instructions': 'Proceed to card payment gateway.',
                'transaction_reference': transaction.transaction_reference
            }
        else:
            return {
                'method': payment_method,
                'transaction_reference': transaction.transaction_reference
            }


class MyAdBoostsView(generics.ListAPIView):
    """
    API endpoint to list user's ad boosts.
    GET: List authenticated user's ad boosts.
    """
    
    serializer_class = AdBoostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's ad boosts."""
        return AdBoost.objects.filter(
            ad__seller=self.request.user
        ).select_related('ad').order_by('-created_at')


class PurchaseAdBoostView(APIView):
    """
    API endpoint to purchase an ad boost.
    POST: Initiate ad boost purchase.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Initiate ad boost purchase."""
        serializer = AdBoostPurchaseSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        ad_id = serializer.validated_data['ad_id']
        boost_type = serializer.validated_data['boost_type']
        duration_days = serializer.validated_data['duration_days']
        payment_method = serializer.validated_data['payment_method']
        
        ad = Ad.objects.get(id=ad_id)
        
        # Calculate amount based on boost type and duration
        # This is a placeholder - integrate with actual pricing logic
        pricing = {
            'vip': 499,
            'top': 299,
            'boosted': 199,
            'featured': 399
        }
        amount = pricing.get(boost_type, 0) * (duration_days / 7)
        
        # Create ad boost
        ad_boost = AdBoost.objects.create(
            ad=ad,
            boost_type=boost_type,
            amount=amount
        )
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='ad_boost',
            ad_boost=ad_boost,
            amount=amount,
            payment_method=payment_method,
            status='pending'
        )
        
        # Here you would integrate with payment gateway
        
        return Response({
            'message': 'Ad boost purchase initiated.',
            'ad_boost': AdBoostSerializer(ad_boost).data,
            'transaction': TransactionSerializer(transaction).data,
            'payment_instructions': {
                'method': payment_method,
                'transaction_reference': transaction.transaction_reference
            }
        }, status=status.HTTP_201_CREATED)


class MyTransactionsView(generics.ListAPIView):
    """
    API endpoint to list user's transactions.
    GET: List authenticated user's transactions.
    """
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's transactions."""
        return Transaction.objects.filter(
            user=self.request.user
        ).select_related(
            'subscription', 'ad_boost'
        ).order_by('-created_at')


class TransactionDetailView(generics.RetrieveAPIView):
    """
    API endpoint for transaction details.
    GET: Retrieve transaction details.
    """
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's transactions."""
        return Transaction.objects.filter(user=self.request.user)


class PaymentCallbackView(APIView):
    """
    API endpoint for payment gateway callbacks.
    POST: Handle payment callback from gateway.
    """
    
    permission_classes = [permissions.AllowAny]  # Gateway will call this
    
    def post(self, request):
        """Handle payment callback."""
        serializer = PaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        transaction_reference = serializer.validated_data['transaction_reference']
        payment_status = serializer.validated_data['status']
        provider_reference = serializer.validated_data.get('payment_provider_reference', '')
        metadata = serializer.validated_data.get('metadata', {})
        
        try:
            transaction = Transaction.objects.get(
                transaction_reference=transaction_reference
            )
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update transaction
        transaction.payment_provider_reference = provider_reference
        transaction.metadata = metadata
        
        if payment_status == 'completed':
            transaction.mark_completed()
        else:
            transaction.status = 'failed'
            transaction.save()
        
        return Response({
            'message': 'Payment callback processed.',
            'transaction': TransactionSerializer(transaction).data
        }, status=status.HTTP_200_OK)


class CancelSubscriptionView(APIView):
    """
    API endpoint to cancel a subscription.
    POST: Cancel active subscription.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """Cancel subscription."""
        subscription = get_object_or_404(
            PremiumSubscription,
            pk=pk,
            user=request.user,
            status='active'
        )
        
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save()
        
        # Update user premium status if no active subscriptions
        active_subscriptions = PremiumSubscription.objects.filter(
            user=request.user,
            status='active'
        ).exists()
        
        if not active_subscriptions:
            request.user.is_premium = False
            request.user.save()
        
        return Response({
            'message': 'Subscription cancelled successfully.',
            'subscription': PremiumSubscriptionSerializer(subscription).data
        }, status=status.HTTP_200_OK)


class ActiveSubscriptionView(APIView):
    """
    API endpoint to get user's active subscription.
    GET: Get current active subscription.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get active subscription."""
        subscription = PremiumSubscription.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-end_date').first()
        
        if subscription:
            return Response(
                PremiumSubscriptionSerializer(subscription).data,
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'message': 'No active subscription.'},
            status=status.HTTP_404_NOT_FOUND
        )