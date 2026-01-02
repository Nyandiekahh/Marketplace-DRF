"""
Views for the categories app.
"""

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache

from .models import Category
from .serializers import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryCreateUpdateSerializer
)


class CategoryListView(generics.ListAPIView):
    """
    API endpoint to list all root categories with their subcategories.
    GET: List all active root categories (categories without parent).
    """
    
    serializer_class = CategoryListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return only root categories (no parent)."""
        return Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).prefetch_related('subcategories')
    
    def list(self, request, *args, **kwargs):
        """List categories with caching."""
        cache_key = 'categories_list'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Cache for 1 hour
        cache.set(cache_key, serializer.data, 3600)
        
        return Response(serializer.data)


class CategoryDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a specific category.
    GET: Retrieve category details by slug or ID.
    """
    
    serializer_class = CategoryDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Return active categories."""
        return Category.objects.filter(is_active=True).select_related('parent')


class AllCategoriesView(APIView):
    """
    API endpoint to list all categories in a flat structure.
    GET: List all active categories (useful for dropdowns).
    """
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Return all categories in flat list."""
        cache_key = 'all_categories_flat'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        categories = Category.objects.filter(is_active=True).order_by('name')
        data = [
            {
                'id': cat.id,
                'name': str(cat),  # Shows hierarchy
                'slug': cat.slug,
                'parent_id': cat.parent_id if cat.parent else None
            }
            for cat in categories
        ]
        
        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        
        return Response(data)


class CategoryCreateView(generics.CreateAPIView):
    """
    API endpoint to create a new category.
    POST: Create a category (admin only).
    """
    
    serializer_class = CategoryCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Category.objects.all()
    
    def perform_create(self, serializer):
        """Clear cache after creating category."""
        serializer.save()
        cache.delete('categories_list')
        cache.delete('all_categories_flat')


class CategoryUpdateView(generics.UpdateAPIView):
    """
    API endpoint to update a category.
    PUT/PATCH: Update a category (admin only).
    """
    
    serializer_class = CategoryCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Category.objects.all()
    lookup_field = 'slug'
    
    def perform_update(self, serializer):
        """Clear cache after updating category."""
        serializer.save()
        cache.delete('categories_list')
        cache.delete('all_categories_flat')


class CategoryDeleteView(generics.DestroyAPIView):
    """
    API endpoint to delete a category.
    DELETE: Soft delete a category (admin only).
    """
    
    permission_classes = [permissions.IsAdminUser]
    queryset = Category.objects.all()
    lookup_field = 'slug'
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()
        cache.delete('categories_list')
        cache.delete('all_categories_flat')