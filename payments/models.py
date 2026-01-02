"""
Models for the payments app.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta


class PremiumSubscription(models.Model):
    """
    Model for premium user subscriptions.
    """
    
    SUBSCRIPTION_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='premium_subscriptions',
        verbose_name='User'
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPE_CHOICES,
        default='premium',
        verbose_name='Subscription Type'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Amount Paid'
    )
    currency = models.CharField(
        max_length=3,
        default='KES',
        verbose_name='Currency'
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Start Date'
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='End Date'
    )
    auto_renew = models.BooleanField(
        default=False,
        verbose_name='Auto Renew'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Premium Subscription'
        verbose_name_plural = 'Premium Subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_type} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True
    
    def activate(self, duration_days=30):
        """Activate subscription."""
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=duration_days)
        self.save()
        
        # Update user premium status
        self.user.is_premium = True
        self.user.save()


class AdBoost(models.Model):
    """
    Model for ad boost purchases.
    """
    
    BOOST_TYPE_CHOICES = [
        ('vip', 'VIP Ad'),
        ('top', 'Top Ad'),
        ('boosted', 'Boosted'),
        ('featured', 'Featured'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending', 'Pending Payment'),
    ]
    
    ad = models.ForeignKey(
        'ads.Ad',
        on_delete=models.CASCADE,
        related_name='boosts',
        verbose_name='Advertisement'
    )
    boost_type = models.CharField(
        max_length=20,
        choices=BOOST_TYPE_CHOICES,
        verbose_name='Boost Type'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Amount Paid'
    )
    currency = models.CharField(
        max_length=3,
        default='KES',
        verbose_name='Currency'
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Start Date'
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='End Date'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ad Boost'
        verbose_name_plural = 'Ad Boosts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ad', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.ad.title} - {self.boost_type} ({self.status})"
    
    @property
    def is_active(self):
        """Check if boost is currently active."""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True
    
    def activate(self, duration_days=7):
        """Activate boost."""
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=duration_days)
        self.save()
        
        # Update ad premium type
        self.ad.premium_type = self.boost_type
        self.ad.save()


class Transaction(models.Model):
    """
    Model for payment transactions.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('ad_boost', 'Ad Boost'),
        ('featured_ad', 'Featured Ad'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='User'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Transaction Type'
    )
    subscription = models.ForeignKey(
        PremiumSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Related Subscription'
    )
    ad_boost = models.ForeignKey(
        AdBoost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Related Ad Boost'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Amount'
    )
    currency = models.CharField(
        max_length=3,
        default='KES',
        verbose_name='Currency'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Payment Method'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    transaction_reference = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='Transaction Reference'
    )
    payment_provider_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Payment Provider Reference'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Generate transaction reference if not set."""
        if not self.transaction_reference:
            import secrets
            self.transaction_reference = f"TXN-{timezone.now().strftime('%Y%m%d')}-{secrets.token_hex(8).upper()}"
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """Mark transaction as completed and activate related items."""
        self.status = 'completed'
        self.save()
        
        # Activate subscription or ad boost
        if self.subscription:
            self.subscription.activate()
        elif self.ad_boost:
            self.ad_boost.activate()


class PricingPlan(models.Model):
    """
    Model for pricing plans.
    """
    
    PLAN_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('ad_boost', 'Ad Boost'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name='Plan Name'
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPE_CHOICES,
        verbose_name='Plan Type'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Price'
    )
    currency = models.CharField(
        max_length=3,
        default='KES',
        verbose_name='Currency'
    )
    duration_days = models.IntegerField(
        default=30,
        verbose_name='Duration (Days)'
    )
    features = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Features',
        help_text='List of features included in this plan'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Display Order'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pricing Plan'
        verbose_name_plural = 'Pricing Plans'
        ordering = ['order', 'price']
    
    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}"