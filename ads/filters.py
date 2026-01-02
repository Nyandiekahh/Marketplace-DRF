"""
Filters for the ads app.
"""

from django_filters import rest_framework as filters
from .models import Ad


class AdFilter(filters.FilterSet):
    """
    FilterSet for ads with comprehensive filtering options.
    """
    
    # Price filters
    price_min = filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Category filters
    category = filters.NumberFilter(field_name='category__id')
    category_slug = filters.CharFilter(field_name='category__slug')
    
    # Location filters
    city = filters.CharFilter(field_name='location__city', lookup_expr='iexact')
    county = filters.CharFilter(field_name='location__county', lookup_expr='iexact')
    
    # Condition filter
    condition = filters.ChoiceFilter(choices=Ad.CONDITION_CHOICES)
    
    # Premium filter
    is_premium = filters.BooleanFilter(method='filter_is_premium')
    premium_type = filters.ChoiceFilter(choices=Ad.PREMIUM_CHOICES)
    
    # Seller filter
    seller = filters.NumberFilter(field_name='seller__id')
    
    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Search filter
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Ad
        fields = [
            'status', 'condition', 'is_negotiable',
            'category', 'price_min', 'price_max'
        ]
    
    def filter_is_premium(self, queryset, name, value):
        """Filter ads by premium status."""
        if value:
            return queryset.exclude(premium_type='basic')
        return queryset.filter(premium_type='basic')
    
    def filter_search(self, queryset, name, value):
        """
        Search filter for title and description.
        For better search, use Elasticsearch in production.
        """
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value)
        )


from django.db import models