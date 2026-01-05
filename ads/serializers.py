from rest_framework import serializers
from .models import Ad, Image, Favorite
from categories.serializers import CategorySerializer
from users.models import CustomUser

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'order', 'created_at']

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number']

class AdListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'slug', 'title', 'price', 'currency', 'condition',
            'primary_image', 'is_favorited', 'location', 'category',
            'status', 'premium_type', 'created_at', 'views_count'
        ]

    def get_primary_image(self, obj):
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url if first_image.image else None
        return None

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, ad=obj).exists()
        return False

    def get_location(self, obj):
        if obj.location:
            return {
                'city': obj.location.city,
                'county': obj.location.county,
                'country': obj.location.country
            }
        return None

class AdDetailSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    seller = SellerSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    location = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            'id', 'slug', 'title', 'description', 'price', 'currency',
            'condition', 'category', 'location', 'seller', 'images',
            'status', 'premium_type', 'is_negotiable', 'views_count',
            'contact_count', 'created_at', 'updated_at', 'is_owner'
        ]

    def get_location(self, obj):
        if obj.location:
            return {
                'city': obj.location.city,
                'county': obj.location.county,
                'country': obj.location.country
            }
        return None

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.seller == request.user
        return False

class AdCreateSerializer(serializers.ModelSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    location_data = serializers.JSONField(write_only=True, required=False)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Ad
        fields = [
            'title', 'description', 'price', 'currency', 'condition',
            'category_id', 'is_negotiable', 'uploaded_images', 'location_data'
        ]

    def create(self, validated_data):
        from users.models import Location
        from categories.models import Category
        
        uploaded_images = validated_data.pop('uploaded_images', [])
        location_data = validated_data.pop('location_data', None)
        category_id = validated_data.pop('category_id')
        
        # Get category
        try:
            category = Category.objects.get(id=category_id)
            validated_data['category'] = category
        except Category.DoesNotExist:
            raise serializers.ValidationError({'category_id': 'Invalid category'})
        
        # Handle location
        if location_data:
            location, _ = Location.objects.get_or_create(
                city=location_data.get('city'),
                county=location_data.get('county'),
                country=location_data.get('country', 'Kenya')
            )
            validated_data['location'] = location

        # Create the ad
        ad = Ad.objects.create(**validated_data)

        # Create images
        for idx, image in enumerate(uploaded_images):
            Image.objects.create(ad=ad, image=image, order=idx)

        return ad

class FavoriteSerializer(serializers.ModelSerializer):
    ad = AdListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'ad', 'created_at']
