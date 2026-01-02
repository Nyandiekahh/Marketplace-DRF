"""
Serializers for the moderation app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Report, Review, VerificationBadge, ContentFlag

User = get_user_model()


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing reports."""
    
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reporter_email', 'report_type',
            'reported_ad', 'reported_user', 'reported_message',
            'reason', 'description', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'reporter', 'status', 'created_at']
    
    def validate(self, attrs):
        """Validate that exactly one reported object is set."""
        reported_objects = [
            attrs.get('reported_ad'),
            attrs.get('reported_user'),
            attrs.get('reported_message')
        ]
        
        if sum(1 for obj in reported_objects if obj is not None) != 1:
            raise serializers.ValidationError(
                "Exactly one of reported_ad, reported_user, or reported_message must be set."
            )
        
        # Set report_type based on which object is reported
        if attrs.get('reported_ad'):
            attrs['report_type'] = 'ad'
        elif attrs.get('reported_user'):
            attrs['report_type'] = 'user'
        elif attrs.get('reported_message'):
            attrs['report_type'] = 'message'
        
        return attrs
    
    def create(self, validated_data):
        """Create report with reporter from request."""
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class ReportDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed report view (admin)."""
    
    reporter = serializers.StringRelatedField()
    resolved_by = serializers.StringRelatedField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'report_type', 'reported_ad',
            'reported_user', 'reported_message', 'reason',
            'description', 'status', 'admin_notes',
            'resolved_by', 'resolved_at', 'created_at', 'updated_at'
        ]


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing reviews."""
    
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewer_name', 'reviewer_email',
            'reviewed_user', 'ad', 'rating', 'comment',
            'is_seller_review', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value
    
    def validate(self, attrs):
        """Validate that user is not reviewing themselves."""
        request = self.context['request']
        reviewed_user = attrs.get('reviewed_user')
        
        if request.user == reviewed_user:
            raise serializers.ValidationError(
                "You cannot review yourself."
            )
        
        # Check if review already exists
        ad = attrs.get('ad')
        if ad:
            existing = Review.objects.filter(
                reviewer=request.user,
                reviewed_user=reviewed_user,
                ad=ad
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    "You have already reviewed this user for this ad."
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create review with reviewer from request."""
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)


class UserReviewsSummarySerializer(serializers.Serializer):
    """Serializer for user reviews summary."""
    
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    rating_distribution = serializers.DictField()
    recent_reviews = ReviewSerializer(many=True)


class VerificationBadgeSerializer(serializers.ModelSerializer):
    """Serializer for verification badges."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    verified_by_email = serializers.EmailField(source='verified_by.email', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = VerificationBadge
        fields = [
            'id', 'user', 'user_email', 'badge_type',
            'verified_by', 'verified_by_email', 'notes',
            'granted_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = ['id', 'verified_by', 'granted_at']


class ContentFlagSerializer(serializers.ModelSerializer):
    """Serializer for content flags."""
    
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True)
    
    class Meta:
        model = ContentFlag
        fields = [
            'id', 'ad', 'ad_title', 'flag_type',
            'confidence_score', 'details', 'is_reviewed',
            'reviewed_by', 'reviewed_by_email', 'created_at',
            'reviewed_at'
        ]
        read_only_fields = [
            'id', 'reviewed_by', 'created_at', 'reviewed_at'
        ]