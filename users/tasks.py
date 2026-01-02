"""
Celery tasks for the users app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from twilio.rest import Client
import os

User = get_user_model()


@shared_task
def send_verification_email(user_id):
    """
    Send email verification code to user.
    
    Args:
        user_id: ID of the user to send verification email to
    """
    try:
        user = User.objects.get(id=user_id)
        verification = user.verification
        
        subject = 'Verify Your Email - Marketplace'
        message = f"""
        Hello {user.get_full_name()},
        
        Thank you for registering with Marketplace!
        
        Your email verification code is: {verification.email_verification_code}
        
        This code will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        Marketplace Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return f"Verification email sent to {user.email}"
    
    except User.DoesNotExist:
        return f"User with ID {user_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_verification_sms(user_id):
    """
    Send phone verification code via SMS.
    
    Args:
        user_id: ID of the user to send verification SMS to
    """
    try:
        user = User.objects.get(id=user_id)
        
        if not user.phone_number:
            return "User has no phone number"
        
        verification = user.verification
        
        # Initialize Twilio client
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_phone]):
            return "Twilio credentials not configured"
        
        client = Client(account_sid, auth_token)
        
        message = f"Your Marketplace verification code is: {verification.phone_verification_code}. Valid for 24 hours."
        
        client.messages.create(
            body=message,
            from_=twilio_phone,
            to=str(user.phone_number)
        )
        
        return f"Verification SMS sent to {user.phone_number}"
    
    except User.DoesNotExist:
        return f"User with ID {user_id} not found"
    except Exception as e:
        return f"Error sending SMS: {str(e)}"


@shared_task
def send_password_reset_email(user_id):
    """
    Send password reset code to user's email.
    
    Args:
        user_id: ID of the user requesting password reset
    """
    try:
        user = User.objects.get(id=user_id)
        verification = user.verification
        
        subject = 'Password Reset Request - Marketplace'
        message = f"""
        Hello {user.get_full_name()},
        
        We received a request to reset your password.
        
        Your password reset code is: {verification.email_verification_code}
        
        This code will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        
        Best regards,
        Marketplace Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return f"Password reset email sent to {user.email}"
    
    except User.DoesNotExist:
        return f"User with ID {user_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_welcome_email(user_id):
    """
    Send welcome email to newly registered user.
    
    Args:
        user_id: ID of the newly registered user
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = 'Welcome to Marketplace!'
        message = f"""
        Hello {user.get_full_name()},
        
        Welcome to Marketplace! We're excited to have you on board.
        
        You can now:
        - Post classified ads
        - Browse thousands of listings
        - Connect with buyers and sellers
        - Manage your profile and ads
        
        If you have any questions, feel free to contact our support team.
        
        Happy trading!
        
        Best regards,
        Marketplace Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return f"Welcome email sent to {user.email}"
    
    except User.DoesNotExist:
        return f"User with ID {user_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"