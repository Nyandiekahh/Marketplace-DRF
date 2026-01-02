"""
Serializers for the categories app.
"""

from rest_framework import serializers
from .models import Category


class SubCategorySerializer(serializers.ModelSerializer):
    """Serializer for subcategories (nested)."""
    
    ad_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'icon', 'description',
            'ad_count', 'order'
        ]


class CategoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing categories with subcategories."""
    
    subcategories = SubCategorySerializer(many=True, read_only=True)
    ad_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'icon', 'description',
            'subcategories', 'ad_count', 'order'
        ]


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Serializer for category details."""
    
    subcategories = SubCategorySerializer(many=True, read_only=True)
    parent = SubCategorySerializer(read_only=True)
    ad_count = serializers.IntegerField(read_only=True)
    breadcrumb = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'icon', 'description',
            'parent', 'subcategories', 'ad_count',
            'breadcrumb', 'created_at', 'updated_at'
        ]
    
    def get_breadcrumb(self, obj):
        """Get breadcrumb trail."""
        return [
            {'id': cat.id, 'name': cat.name, 'slug': cat.slug}
            for cat in obj.get_breadcrumb()
        ]


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories (admin only)."""
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'icon',
            'description', 'order', 'is_active'
        ]
        extra_kwargs = {
            'slug': {'required': False}
        }
    
    def validate_parent(self, value):
        """Validate that parent is not the same as the category being created/updated."""
        if self.instance and value == self.instance:
            raise serializers.ValidationError(
                "A category cannot be its own parent."
            )
        return value