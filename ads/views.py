"""
Views for the ads app.
"""

from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Ad, Image, Favorite, AdView
from .serializers import (
    AdListSerializer,
    AdDetailSerializer,
    AdCreateSerializer,
    AdUpdateSerializer,
    FavoriteSerializer,
    BoostAdSerializer,
    ImageSerializer
)
from .filters import AdFilter
from .permissions import IsOwnerOrReadOnly


class AdListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating ads.
    GET: List all active ads with filtering.
    POST: Create a new ad (authenticated users only).
    """
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AdFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'views_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.request.method == 'POST':
            return AdCreateSerializer
        return AdListSerializer
    
    def get_queryset(self):
        """
        Return ads based on request method.
        For listing, show only active ads.
        """
        queryset = Ad.objects.filter(status='active').select_related(
            'category', 'location', 'seller'
        ).prefetch_related('images')
        
        # Premium ads first, then by creation date
        queryset = queryset.annotate(
            is_premium_ad=Count('id', filter=~Q(premium_type='basic'))
        ).order_by('-is_premium_ad', '-created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        """Create ad and set seller."""
        serializer.save(seller=self.request.user)


class AdDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for ad details.
    GET: Retrieve ad details and increment view count.
    PUT/PATCH: Update ad (owner only).
    DELETE: Delete ad (owner only).
    """
    
    queryset = Ad.objects.all()
    lookup_field = 'slug'
    permission_classes = [IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.request.method in ['PUT', 'PATCH']:
            return AdUpdateSerializer
        return AdDetailSerializer
    
    def get_queryset(self):
        """Return queryset with related objects."""
        return Ad.objects.select_related(
            'category', 'location', 'seller', 'seller__location'
        ).prefetch_related('images')
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve ad and track view."""
        instance = self.get_object()
        
        # Track view (only if not the owner)
        if not request.user.is_authenticated or request.user != instance.seller:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Create view record
            AdView.objects.create(
                ad=instance,
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Increment view count
            instance.increment_views()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        """Soft delete by setting status to deleted."""
        instance.status = 'deleted'
        instance.save()


class MyAdsView(generics.ListAPIView):
    """
    API endpoint to list current user's ads.
    GET: List all ads created by the authenticated user.
    """
    
    serializer_class = AdListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status', 'views_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's ads."""
        return Ad.objects.filter(
            seller=self.request.user
        ).exclude(
            status='deleted'
        ).select_related('category', 'location').prefetch_related('images')


class AdSearchView(generics.ListAPIView):
    """
    API endpoint for searching ads.
    GET: Search ads by query with advanced filtering.
    """
    
    serializer_class = AdListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AdFilter
    ordering_fields = ['created_at', 'price', 'views_count']
    
    def get_queryset(self):
        """Search ads based on query parameter."""
        query = self.request.query_params.get('q', '')
        
        queryset = Ad.objects.filter(status='active')
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        return queryset.select_related(
            'category', 'location', 'seller'
        ).prefetch_related('images')


class FavoriteListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for user favorites.
    GET: List user's favorited ads.
    POST: Add ad to favorites.
    """
    
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's favorites."""
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('ad', 'ad__category', 'ad__location')


class FavoriteDestroyView(generics.DestroyAPIView):
    """
    API endpoint to remove ad from favorites.
    DELETE: Remove favorite.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's favorites."""
        return Favorite.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Remove favorite by ad ID."""
        ad_id = kwargs.get('pk')
        try:
            favorite = Favorite.objects.get(
                user=request.user,
                ad_id=ad_id
            )
            favorite.delete()
            return Response(
                {'message': 'Removed from favorites.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Favorite.DoesNotExist:
            return Response(
                {'error': 'Favorite not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class BoostAdView(APIView):
    """
    API endpoint to boost ad to premium.
    POST: Upgrade ad to premium status.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, slug):
        """Boost ad to premium."""
        ad = get_object_or_404(Ad, slug=slug, seller=request.user)
        
        serializer = BoostAdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        premium_type = serializer.validated_data['premium_type']
        duration_days = serializer.validated_data['duration_days']
        
        # Here you would integrate payment processing
        # For now, we'll just update the ad
        
        ad.premium_type = premium_type
        ad.expires_at = timezone.now() + timezone.timedelta(days=duration_days)
        ad.save()
        
        return Response({
            'message': f'Ad boosted to {premium_type} for {duration_days} days.',
            'ad': AdDetailSerializer(ad, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class MarkAsSoldView(APIView):
    """
    API endpoint to mark ad as sold.
    POST: Mark ad as sold.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, slug):
        """Mark ad as sold."""
        ad = get_object_or_404(Ad, slug=slug, seller=request.user)
        
        if ad.status == 'sold':
            return Response(
                {'error': 'Ad is already marked as sold.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ad.status = 'sold'
        ad.save()
        
        return Response({
            'message': 'Ad marked as sold.',
            'ad': AdDetailSerializer(ad, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class ReactivateAdView(APIView):
    """
    API endpoint to reactivate an expired ad.
    POST: Reactivate ad.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, slug):
        """Reactivate ad."""
        ad = get_object_or_404(Ad, slug=slug, seller=request.user)
        
        if ad.status not in ['expired', 'sold']:
            return Response(
                {'error': 'Only expired or sold ads can be reactivated.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.conf import settings
        ad.status = 'active'
        ad.expires_at = timezone.now() + timezone.timedelta(
            days=settings.AD_EXPIRATION_DAYS
        )
        ad.save()
        
        return Response({
            'message': 'Ad reactivated successfully.',
            'ad': AdDetailSerializer(ad, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class DeleteImageView(APIView):
    """
    API endpoint to delete ad image.
    DELETE: Remove image from ad.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, slug, image_id):
        """Delete ad image."""
        ad = get_object_or_404(Ad, slug=slug, seller=request.user)
        
        try:
            image = Image.objects.get(id=image_id, ad=ad)
            image.delete()
            return Response(
                {'message': 'Image deleted successfully.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Image.DoesNotExist:
            return Response(
                {'error': 'Image not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class IncrementContactView(APIView):
    """
    API endpoint to track when user contacts seller.
    POST: Increment contact count.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, slug):
        """Increment contact count."""
        ad = get_object_or_404(Ad, slug=slug, status='active')
        
        # Don't increment if user is the owner
        if request.user == ad.seller:
            return Response(
                {'error': 'Cannot contact your own ad.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ad.increment_contacts()
        
        return Response({
            'message': 'Contact tracked.',
            'contact_count': ad.contact_count
        }, status=status.HTTP_200_OK)


class SimilarAdsView(generics.ListAPIView):
    """
    API endpoint to get similar ads.
    GET: Get ads similar to the specified ad.
    """
    
    serializer_class = AdListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get similar ads based on category and location."""
        slug = self.kwargs.get('slug')
        ad = get_object_or_404(Ad, slug=slug)
        
        # Get ads in same category and location (excluding current ad)
        similar_ads = Ad.objects.filter(
            category=ad.category,
            status='active'
        ).exclude(
            id=ad.id
        ).select_related(
            'category', 'location', 'seller'
        ).prefetch_related('images')[:10]
        
        return similar_ads