"""
URL configuration for ads app.
"""

from django.urls import path
from .views import (
    AdListCreateView,
    AdDetailView,
    MyAdsView,
    AdSearchView,
    FavoriteListCreateView,
    FavoriteDestroyView,
    BoostAdView,
    MarkAsSoldView,
    ReactivateAdView,
    DeleteImageView,
    IncrementContactView,
    SimilarAdsView,
)

app_name = 'ads'

urlpatterns = [
    # Ad CRUD
    path('', AdListCreateView.as_view(), name='ad_list_create'),
    path('my-ads/', MyAdsView.as_view(), name='my_ads'),
    path('search/', AdSearchView.as_view(), name='ad_search'),
    path('<slug:slug>/', AdDetailView.as_view(), name='ad_detail'),
    path('<slug:slug>/similar/', SimilarAdsView.as_view(), name='similar_ads'),
    
    # Ad actions
    path('<slug:slug>/boost/', BoostAdView.as_view(), name='boost_ad'),
    path('<slug:slug>/mark-sold/', MarkAsSoldView.as_view(), name='mark_sold'),
    path('<slug:slug>/reactivate/', ReactivateAdView.as_view(), name='reactivate_ad'),
    path('<slug:slug>/contact/', IncrementContactView.as_view(), name='increment_contact'),
    
    # Image management
    path('<slug:slug>/images/<int:image_id>/delete/', DeleteImageView.as_view(), name='delete_image'),
    
    # Favorites
    path('favorites/', FavoriteListCreateView.as_view(), name='favorites'),
    path('favorites/<int:pk>/', FavoriteDestroyView.as_view(), name='remove_favorite'),
]