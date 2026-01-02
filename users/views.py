"""
Views for the users app.
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from .models import UserVerification, BlockedUser
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    VerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    BlockUserSerializer
)
from .tasks import send_verification_email, send_verification_sms, send_password_reset_email

User = get_user_model()


class RegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    POST: Create a new user account.
    """
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create user and send verification email/SMS."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email and SMS
        send_verification_email.delay(user.id)
        if user.phone_number:
            send_verification_sms.delay(user.id)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please verify your email and phone number.'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API endpoint for user login.
    POST: Authenticate user and return JWT tokens.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Authenticate user and return tokens."""
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """
    API endpoint for email verification.
    POST: Verify user's email with verification code.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Verify email with provided code."""
        serializer = VerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        user = request.user
        
        try:
            verification = user.verification
        except UserVerification.DoesNotExist:
            return Response(
                {'error': 'Verification record not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if code is expired (valid for 24 hours)
        if verification.email_code_expires and \
           timezone.now() > verification.email_code_expires:
            return Response(
                {'error': 'Verification code has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify code
        if verification.email_verification_code == code:
            verification.email_verified = True
            verification.save()
            
            user.is_verified = True
            user.save()
            
            return Response({
                'message': 'Email verified successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Invalid verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyPhoneView(APIView):
    """
    API endpoint for phone verification.
    POST: Verify user's phone with verification code.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Verify phone with provided code."""
        serializer = VerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        user = request.user
        
        try:
            verification = user.verification
        except UserVerification.DoesNotExist:
            return Response(
                {'error': 'Verification record not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if code is expired (valid for 24 hours)
        if verification.phone_code_expires and \
           timezone.now() > verification.phone_code_expires:
            return Response(
                {'error': 'Verification code has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify code
        if verification.phone_verification_code == code:
            verification.phone_verified = True
            verification.save()
            
            return Response({
                'message': 'Phone verified successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Invalid verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResendVerificationView(APIView):
    """
    API endpoint to resend verification code.
    POST: Resend email or phone verification code.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Resend verification code."""
        verification_type = request.data.get('verification_type')
        
        if verification_type not in ['email', 'phone']:
            return Response(
                {'error': 'Invalid verification type.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        verification = user.verification
        
        # Generate new code and update expiry
        if verification_type == 'email':
            verification.email_verification_code = UserVerification.generate_verification_code()
            verification.email_code_expires = timezone.now() + timedelta(hours=24)
            verification.save()
            send_verification_email.delay(user.id)
        else:
            verification.phone_verification_code = UserVerification.generate_verification_code()
            verification.phone_code_expires = timezone.now() + timedelta(hours=24)
            verification.save()
            send_verification_sms.delay(user.id)
        
        return Response({
            'message': f'{verification_type.capitalize()} verification code sent.'
        }, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for user profile.
    GET: Retrieve authenticated user's profile.
    PUT/PATCH: Update authenticated user's profile.
    """
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the authenticated user."""
        return self.request.user


class PasswordResetRequestView(APIView):
    """
    API endpoint to request password reset.
    POST: Send password reset code to user's email.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send password reset code."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate reset code
        verification, _ = UserVerification.objects.get_or_create(user=user)
        verification.email_verification_code = UserVerification.generate_verification_code()
        verification.email_code_expires = timezone.now() + timedelta(hours=1)
        verification.save()
        
        # Send reset email
        send_password_reset_email.delay(user.id)
        
        return Response({
            'message': 'Password reset code sent to your email.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    API endpoint to confirm password reset.
    POST: Reset password with verification code.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Reset password with code."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']
        
        # Find user with this code
        try:
            verification = UserVerification.objects.get(
                email_verification_code=code
            )
        except UserVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if code is expired
        if verification.email_code_expires and \
           timezone.now() > verification.email_code_expires:
            return Response(
                {'error': 'Verification code has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password
        user = verification.user
        user.set_password(new_password)
        user.save()
        
        # Clear verification code
        verification.email_verification_code = ''
        verification.email_code_expires = None
        verification.save()
        
        return Response({
            'message': 'Password reset successfully.'
        }, status=status.HTTP_200_OK)


class BlockUserView(generics.CreateAPIView):
    """
    API endpoint to block a user.
    POST: Block a user.
    """
    
    serializer_class = BlockUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return blocked users for the authenticated user."""
        return BlockedUser.objects.filter(blocker=self.request.user)


class BlockedUsersListView(generics.ListAPIView):
    """
    API endpoint to list blocked users.
    GET: List all users blocked by the authenticated user.
    """
    
    serializer_class = BlockUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return blocked users for the authenticated user."""
        return BlockedUser.objects.filter(blocker=self.request.user)


class UnblockUserView(generics.DestroyAPIView):
    """
    API endpoint to unblock a user.
    DELETE: Unblock a user.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk):
        """Unblock a user."""
        try:
            blocked_user = BlockedUser.objects.get(
                blocker=request.user,
                blocked_id=pk
            )
            blocked_user.delete()
            return Response(
                {'message': 'User unblocked successfully.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except BlockedUser.DoesNotExist:
            return Response(
                {'error': 'Blocked user not found.'},
                status=status.HTTP_404_NOT_FOUND
            )