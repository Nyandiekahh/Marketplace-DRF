"""
Models for the moderation app.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Report(models.Model):
    """
    Model for reporting ads, users, or messages.
    """
    
    REPORT_TYPE_CHOICES = [
        ('ad', 'Advertisement'),
        ('user', 'User'),
        ('message', 'Message'),
    ]
    
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('fraud', 'Fraud/Scam'),
        ('inappropriate', 'Inappropriate Content'),
        ('duplicate', 'Duplicate Listing'),
        ('wrong_category', 'Wrong Category'),
        ('harassment', 'Harassment'),
        ('fake', 'Fake/Counterfeit'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name='Reporter'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name='Report Type'
    )
    
    # Related objects (only one should be set)
    reported_ad = models.ForeignKey(
        'ads.Ad',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='Reported Ad'
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports_received',
        verbose_name='Reported User'
    )
    reported_message = models.ForeignKey(
        'messages.Message',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='Reported Message'
    )
    
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        verbose_name='Reason'
    )
    description = models.TextField(
        verbose_name='Description',
        help_text='Provide details about the issue'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    admin_notes = models.TextField(
        blank=True,
        verbose_name='Admin Notes'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_resolved',
        verbose_name='Resolved By'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Resolved At'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['reporter']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} report by {self.reporter.email}"
    
    def resolve(self, admin_user, notes=''):
        """Mark report as resolved."""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_by = admin_user
        self.resolved_at = timezone.now()
        self.admin_notes = notes
        self.save()


class Review(models.Model):
    """
    Model for user reviews/ratings.
    Users can review other users after transactions.
    """
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        verbose_name='Reviewer'
    )
    reviewed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        verbose_name='Reviewed User'
    )
    ad = models.ForeignKey(
        'ads.Ad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name='Related Ad'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating (1-5)'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Comment'
    )
    is_seller_review = models.BooleanField(
        default=True,
        verbose_name='Is Seller Review',
        help_text='True if reviewing as seller, False if reviewing as buyer'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['reviewer', 'reviewed_user', 'ad']
        indexes = [
            models.Index(fields=['reviewed_user', '-created_at']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.reviewer.email} rated {self.reviewed_user.email}: {self.rating}/5"


class VerificationBadge(models.Model):
    """
    Model for user verification badges.
    Admins can assign badges to trusted users.
    """
    
    BADGE_TYPE_CHOICES = [
        ('email_verified', 'Email Verified'),
        ('phone_verified', 'Phone Verified'),
        ('id_verified', 'ID Verified'),
        ('trusted_seller', 'Trusted Seller'),
        ('power_seller', 'Power Seller'),
        ('verified_buyer', 'Verified Buyer'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name='User'
    )
    badge_type = models.CharField(
        max_length=50,
        choices=BADGE_TYPE_CHOICES,
        verbose_name='Badge Type'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badges_verified',
        verbose_name='Verified By'
    )
    notes = models.TextField(blank=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expires At'
    )
    
    class Meta:
        verbose_name = 'Verification Badge'
        verbose_name_plural = 'Verification Badges'
        unique_together = ['user', 'badge_type']
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_badge_type_display()}"
    
    @property
    def is_expired(self):
        """Check if badge has expired."""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


class ContentFlag(models.Model):
    """
    Model for automated content flagging.
    System flags suspicious content for review.
    """
    
    FLAG_TYPE_CHOICES = [
        ('suspicious_keywords', 'Suspicious Keywords'),
        ('low_quality_images', 'Low Quality Images'),
        ('price_anomaly', 'Price Anomaly'),
        ('duplicate_content', 'Duplicate Content'),
        ('external_links', 'External Links'),
        ('contact_info_in_description', 'Contact Info in Description'),
    ]
    
    ad = models.ForeignKey(
        'ads.Ad',
        on_delete=models.CASCADE,
        related_name='flags',
        verbose_name='Flagged Ad'
    )
    flag_type = models.CharField(
        max_length=50,
        choices=FLAG_TYPE_CHOICES,
        verbose_name='Flag Type'
    )
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='Confidence Score'
    )
    details = models.TextField(
        blank=True,
        verbose_name='Details'
    )
    is_reviewed = models.BooleanField(
        default=False,
        verbose_name='Is Reviewed'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flags_reviewed',
        verbose_name='Reviewed By'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Reviewed At'
    )
    
    class Meta:
        verbose_name = 'Content Flag'
        verbose_name_plural = 'Content Flags'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_reviewed', '-created_at']),
            models.Index(fields=['flag_type']),
        ]
    
    def __str__(self):
        return f"{self.get_flag_type_display()} - {self.ad.title}"