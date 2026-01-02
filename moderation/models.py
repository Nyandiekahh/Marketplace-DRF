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
        'chat_messages.Message',  # Changed from 'messages.Message'
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
    
    def __str__(self):
        return f"{self.get_report_type_display()} report by {self.reporter.email}"


class Review(models.Model):
    """
    Model for user reviews/ratings.
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
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer.email} rated {self.reviewed_user.email}: {self.rating}/5"
