"""
Serializers for the users app.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import CustomUser, Location, UserVerification, BlockedUser


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model."""
    
    class Meta:
        model = Location
        fields = ['id', 'city', 'county', 'country']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    location = LocationSerializer(required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'password', 'password2',
            'first_name', 'last_name', 'phone_number', 'location'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()
    
    def validate_phone_number(self, value):
        """Validate phone number uniqueness."""
        if value and CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value
    
    def create(self, validated_data):
        """Create and return a new user."""
        validated_data.pop('password2')
        location_data = validated_data.pop('location', None)
        
        # Create location if provided
        location = None
        if location_data:
            location, _ = Location.objects.get_or_create(**location_data)
        
        # Create user
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number'),
            location=location
        )
        
        # Create verification record
        UserVerification.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate credentials and return user."""
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile viewing and updating."""
    
    location = LocationSerializer(required=False)
    active_ads_count = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'location', 'profile_picture',
            'bio', 'is_verified', 'is_premium', 'joined_date',
            'active_ads_count'
        ]
        read_only_fields = [
            'id', 'email', 'is_verified', 'is_premium', 'joined_date'
        ]
    
    def update(self, instance, validated_data):
        """Update user profile."""
        location_data = validated_data.pop('location', None)
        
        if location_data:
            location, _ = Location.objects.get_or_create(**location_data)
            instance.location = location
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class VerificationSerializer(serializers.Serializer):
    """Serializer for email/phone verification."""
    
    code = serializers.CharField(max_length=6, min_length=6)
    verification_type = serializers.ChoiceField(
        choices=['email', 'phone'],
        required=True
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate that user with email exists."""
        try:
            CustomUser.objects.get(email=value.lower())
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "No user found with this email address."
            )
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs


class BlockUserSerializer(serializers.ModelSerializer):
    """Serializer for blocking users."""
    
    blocked_email = serializers.EmailField(write_only=True)
    
    class Meta:
        model = BlockedUser
        fields = ['id', 'blocked_email', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_blocked_email(self, value):
        """Validate that the user to block exists."""
        try:
            CustomUser.objects.get(email=value.lower())
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "No user found with this email address."
            )
        return value.lower()
    
    def create(self, validated_data):
        """Create a block relationship."""
        blocker = self.context['request'].user
        blocked_email = validated_data.pop('blocked_email')
        blocked = CustomUser.objects.get(email=blocked_email)
        
        if blocker == blocked:
            raise serializers.ValidationError(
                "You cannot block yourself."
            )
        
        blocked_user, created = BlockedUser.objects.get_or_create(
            blocker=blocker,
            blocked=blocked,
            defaults={'reason': validated_data.get('reason', '')}
        )
        
        return blocked_user