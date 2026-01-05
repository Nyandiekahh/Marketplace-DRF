from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from .models import Ad, Image, Favorite
from .serializers import (
    AdListSerializer,
    AdDetailSerializer,
    AdCreateSerializer,
    FavoriteSerializer
)

class AdListView(generics.ListAPIView):
    serializer_class = AdListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Ad.objects.filter(status='active').select_related('category', 'location', 'seller')
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Category filter
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Price range
        price_min = self.request.query_params.get('price_min', None)
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        
        price_max = self.request.query_params.get('price_max', None)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        
        # Condition
        condition = self.request.query_params.get('condition', None)
        if condition:
            queryset = queryset.filter(condition=condition)
        
        return queryset.order_by('-created_at')

class AdDetailView(generics.RetrieveAPIView):
    queryset = Ad.objects.filter(status='active')
    serializer_class = AdDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Ad.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class AdCreateView(generics.CreateAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class AdUpdateView(generics.UpdateAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdCreateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Ad.objects.filter(seller=self.request.user)

class AdDeleteView(generics.DestroyAPIView):
    queryset = Ad.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Ad.objects.filter(seller=self.request.user)

class MyAdsView(generics.ListAPIView):
    serializer_class = AdListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ad.objects.filter(seller=self.request.user).order_by('-created_at')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_favorites(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, ad=ad)
    
    if created:
        return Response({'message': 'Added to favorites'}, status=status.HTTP_201_CREATED)
    return Response({'message': 'Already in favorites'}, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_favorites(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    deleted_count, _ = Favorite.objects.filter(user=request.user, ad=ad).delete()
    
    if deleted_count > 0:
        return Response({'message': 'Removed from favorites'}, status=status.HTTP_204_NO_CONTENT)
    return Response({'message': 'Not in favorites'}, status=status.HTTP_404_NOT_FOUND)

class FavoritesListView(generics.ListAPIView):
    serializer_class = AdListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        favorite_ads = Favorite.objects.filter(user=self.request.user).values_list('ad', flat=True)
        return Ad.objects.filter(id__in=favorite_ads).order_by('-created_at')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_sold(request, slug):
    ad = get_object_or_404(Ad, slug=slug, seller=request.user)
    ad.status = 'sold'
    ad.save()
    return Response({'message': 'Ad marked as sold'}, status=status.HTTP_200_OK)
