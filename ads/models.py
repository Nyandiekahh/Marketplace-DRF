"""
Models for the ads app.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta

from categories.models import Category
from users.models import Location


class Ad(models.Model):
    """Model for classified advertisements."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('sold', 'Sold'),
        ('deleted', 'Deleted'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]
    
    PREMIUM_CHOICES = [
        ('basic', 'Basic'),
        ('vip', 'VIP'),
        ('top', 'Top Ad'),
        ('boosted', 'Boosted'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Ad Title'
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True
    )
    description = models.TextField(
        verbose_name='Description'
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Price'
    )
    currency = models.CharField(
        max_length=3,
        default='KES',
        verbose_name='Currency'
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='used'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='ads'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ads'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ads'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    premium_type = models.CharField(
        max_length=20,
        choices=PREMIUM_CHOICES,
        default='basic'
    )
    is_negotiable = models.BooleanField(
        default=True,
        verbose_name='Price Negotiable'
    )
    views_count = models.IntegerField(
        default=0,
        verbose_name='View Count'
    )
    contact_count = models.IntegerField(
        default=0,
        verbose_name='Contact Count'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expiration Date'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Advertisement'
        verbose_name_plural = 'Advertisements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['premium_type', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Override save to set expiration date."""
        if not self.expires_at and self.status == 'active':
            self.expires_at = timezone.now() + timedelta(
                days=settings.AD_EXPIRATION_DAYS
            )
        
        if not self.slug:
            from django.utils.text import slugify
            import secrets
            self.slug = f"{slugify(self.title)}-{secrets.token_hex(4)}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if ad has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_premium(self):
        """Check if ad is premium."""
        return self.premium_type != 'basic'
    
    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_contacts(self):
        """Increment contact count."""
        self.contact_count += 1
        self.save(update_fields=['contact_count'])


class Image(models.Model):
    """Model for ad images."""
    
    ad = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='ad_images/',
        verbose_name='Image'
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Alt Text'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Display Order'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.ad.title}"


class Favorite(models.Model):
    """Model for user favorites."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    ad = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        unique_together = ['user', 'ad']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} favorited {self.ad.title}"


class AdView(models.Model):
    """Model for tracking ad views."""
    
    ad = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ad View'
        verbose_name_plural = 'Ad Views'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.ad.title}"