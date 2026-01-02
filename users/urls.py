"""
URL configuration for users app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegistrationView,
    LoginView,
    VerifyEmailView,
    VerifyPhoneView,
    ResendVerificationView,
    ProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    BlockUserView,
    BlockedUsersListView,
    UnblockUserView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Verification
    path('verify/email/', VerifyEmailView.as_view(), name='verify_email'),
    path('verify/phone/', VerifyPhoneView.as_view(), name='verify_phone'),
    path('verify/resend/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Password Reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Blocking
    path('block/', BlockUserView.as_view(), name='block_user'),
    path('blocked/', BlockedUsersListView.as_view(), name='blocked_users'),
    path('unblock/<int:pk>/', UnblockUserView.as_view(), name='unblock_user'),
]