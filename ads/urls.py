from django.urls import path
from . import views

urlpatterns = [
    # List and create ads
    path('', views.AdListView.as_view(), name='ad-list'),
    path('create/', views.AdCreateView.as_view(), name='ad-create'),
    path('my-ads/', views.MyAdsView.as_view(), name='my-ads'),
    
    # Favorites
    path('favorites/', views.FavoritesListView.as_view(), name='favorites-list'),
    path('<int:ad_id>/favorite/', views.add_to_favorites, name='add-favorite'),
    path('<int:ad_id>/unfavorite/', views.remove_from_favorites, name='remove-favorite'),
    
    # Detail, update, delete, mark as sold
    path('<slug:slug>/', views.AdDetailView.as_view(), name='ad-detail'),
    path('<slug:slug>/update/', views.AdUpdateView.as_view(), name='ad-update'),
    path('<slug:slug>/delete/', views.AdDeleteView.as_view(), name='ad-delete'),
    path('<slug:slug>/mark-sold/', views.mark_as_sold, name='mark-sold'),
]
