"""
User models for the marketplace application.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
import secrets


class Location(models.Model):
    """Model for storing location information."""
    
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Kenya')
    
    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        unique_together = ['city', 'county', 'country']
        ordering = ['country', 'county', 'city']
    
    def __str__(self):
        return f"{self.city}, {self.county}, {self.country}"


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Uses email as the primary identifier.
    """
    
    email = models.EmailField(
        unique=True,
        verbose_name='Email Address',
        help_text='Required. Enter a valid email address.'
    )
    phone_number = PhoneNumberField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='Phone Number',
        help_text='Enter phone number in international format (e.g., +254712345678)'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name='Profile Picture'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biography'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Is Verified',
        help_text='Designates whether this user has verified their account.'
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name='Is Premium User',
        help_text='Designates whether this user has a premium subscription.'
    )
    joined_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date Joined'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated'
    )
    
    # Make email the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-joined_date']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def active_ads_count(self):
        """Return the count of active ads for this user."""
        return self.ads.filter(status='active').count()


class UserVerification(models.Model):
    """
    Model for storing user verification information.
    Handles both email and phone verification.
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verification'
    )
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(
        max_length=6,
        blank=True,
        verbose_name='Email Verification Code'
    )
    phone_verification_code = models.CharField(
        max_length=6,
        blank=True,
        verbose_name='Phone Verification Code'
    )
    email_code_expires = models.DateTimeField(null=True, blank=True)
    phone_code_expires = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Verification'
        verbose_name_plural = 'User Verifications'
    
    def __str__(self):
        return f"Verification for {self.user.email}"
    
    @staticmethod
    def generate_verification_code():
        """Generate a random 6-digit verification code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def save(self, *args, **kwargs):
        """Override save to generate codes if empty."""
        if not self.email_verification_code:
            self.email_verification_code = self.generate_verification_code()
        if not self.phone_verification_code:
            self.phone_verification_code = self.generate_verification_code()
        super().save(*args, **kwargs)


class BlockedUser(models.Model):
    """
    Model for managing blocked users.
    Allows users to block other users.
    """
    
    blocker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='blocking',
        verbose_name='User Who Blocked'
    )
    blocked = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='blocked_by',
        verbose_name='Blocked User'
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Blocked User'
        verbose_name_plural = 'Blocked Users'
        unique_together = ['blocker', 'blocked']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"