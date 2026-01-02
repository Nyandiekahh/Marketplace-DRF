"""
Serializers for the ads app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Ad, Image, Favorite, AdView
from categories.serializers import SubCategorySerializer
from users.serializers import LocationSerializer

User = get_user_model()


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for ad images."""
    
    class Meta:
        model = Image
        fields = ['id', 'image', 'alt_text', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class SellerSerializer(serializers.ModelSerializer):
    """Serializer for ad seller information."""
    
    location = LocationSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email',
            'phone_number', 'location', 'profile_picture',
            'is_verified', 'joined_date'
        ]
        read_only_fields = fields


class AdListSerializer(serializers.ModelSerializer):
    """Serializer for listing ads (search results, browse)."""
    
    category = SubCategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Ad
        fields = [
            'id', 'slug', 'title', 'price', 'currency',
            'condition', 'category', 'location', 'primary_image',
            'status', 'premium_type', 'is_negotiable',
            'views_count', 'is_favorited', 'created_at'
        ]
    
    def get_primary_image(self, obj):
        """Get the first/primary image."""
        first_image = obj.images.first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None
    
    def get_is_favorited(self, obj):
        """Check if current user has favorited this ad."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                ad=obj
            ).exists()
        return False


class AdDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed ad view."""
    
    category = SubCategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    seller = SellerSerializer(read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    
    class Meta:
        model = Ad
        fields = [
            'id', 'slug', 'title', 'description', 'price',
            'currency', 'condition', 'category', 'location',
            'seller', 'images', 'status', 'premium_type',
            'is_negotiable', 'views_count', 'contact_count',
            'is_favorited', 'is_owner', 'expires_at',
            'created_at', 'updated_at'
        ]
    
    def get_is_favorited(self, obj):
        """Check if current user has favorited this ad."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                ad=obj
            ).exists()
        return False
    
    def get_is_owner(self, obj):
        """Check if current user is the owner."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.seller == request.user
        return False


class AdCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ads."""
    
    images = ImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False),
        write_only=True,
        required=False,
        max_length=5  # Maximum 5 images
    )
    category_id = serializers.IntegerField(write_only=True)
    location_data = LocationSerializer(write_only=True, required=False)
    
    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'description', 'price', 'currency',
            'condition', 'category_id', 'location_data',
            'is_negotiable', 'status', 'images', 'uploaded_images'
        ]
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value < 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value
    
    def validate_uploaded_images(self, value):
        """Validate uploaded images."""
        if value and len(value) > 5:
            raise serializers.ValidationError("Maximum 5 images allowed per ad.")
        
        # Validate image size (max 5MB per image)
        for image in value:
            if image.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    f"Image {image.name} is too large. Maximum size is 5MB."
                )
        
        return value
    
    def create(self, validated_data):
        """Create ad with images and location."""
        from users.models import Location
        from categories.models import Category
        
        uploaded_images = validated_data.pop('uploaded_images', [])
        location_data = validated_data.pop('location_data', None)
        category_id = validated_data.pop('category_id')
        
        # Get or create location
        location = None
        if location_data:
            location, _ = Location.objects.get_or_create(**location_data)
        
        # Get category
        try:
            category = Category.objects.get(id=category_id, is_active=True)
        except Category.DoesNotExist:
            raise serializers.ValidationError({
                'category_id': 'Invalid category ID.'
            })
        
        # Create ad
        ad = Ad.objects.create(
            category=category,
            location=location,
            seller=self.context['request'].user,
            **validated_data
        )
        
        # Create images
        for idx, image in enumerate(uploaded_images):
            Image.objects.create(
                ad=ad,
                image=image,
                order=idx
            )
        
        return ad


class AdUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ads."""
    
    category_id = serializers.IntegerField(write_only=True, required=False)
    location_data = LocationSerializer(write_only=True, required=False)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False),
        write_only=True,
        required=False,
        max_length=5
    )
    
    class Meta:
        model = Ad
        fields = [
            'title', 'description', 'price', 'currency',
            'condition', 'category_id', 'location_data',
            'is_negotiable', 'status', 'uploaded_images'
        ]
    
    def update(self, instance, validated_data):
        """Update ad."""
        from users.models import Location
        from categories.models import Category
        
        uploaded_images = validated_data.pop('uploaded_images', None)
        location_data = validated_data.pop('location_data', None)
        category_id = validated_data.pop('category_id', None)
        
        # Update location
        if location_data:
            location, _ = Location.objects.get_or_create(**location_data)
            instance.location = location
        
        # Update category
        if category_id:
            try:
                category = Category.objects.get(id=category_id, is_active=True)
                instance.category = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({
                    'category_id': 'Invalid category ID.'
                })
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Add new images if provided
        if uploaded_images:
            current_image_count = instance.images.count()
            if current_image_count + len(uploaded_images) > 5:
                raise serializers.ValidationError(
                    "Total images cannot exceed 5."
                )
            
            for idx, image in enumerate(uploaded_images):
                Image.objects.create(
                    ad=instance,
                    image=image,
                    order=current_image_count + idx
                )
        
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorites."""
    
    ad = AdListSerializer(read_only=True)
    ad_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'ad', 'ad_id', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_ad_id(self, value):
        """Validate that ad exists and is active."""
        try:
            ad = Ad.objects.get(id=value, status='active')
        except Ad.DoesNotExist:
            raise serializers.ValidationError("Ad not found or not active.")
        return value
    
    def create(self, validated_data):
        """Create favorite."""
        ad_id = validated_data.pop('ad_id')
        ad = Ad.objects.get(id=ad_id)
        
        favorite, created = Favorite.objects.get_or_create(
            user=self.context['request'].user,
            ad=ad
        )
        
        return favorite


class BoostAdSerializer(serializers.Serializer):
    """Serializer for boosting ads to premium."""
    
    premium_type = serializers.ChoiceField(
        choices=['vip', 'top', 'boosted']
    )
    duration_days = serializers.IntegerField(
        min_value=1,
        max_value=30,
        default=7
    )
    
    def validate(self, attrs):
        """Validate boost request."""
        # Here you would add payment validation
        # For now, we'll just validate the data
        return attrs