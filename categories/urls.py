"""
URL configuration for categories app.
"""

from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    AllCategoriesView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
)

app_name = 'categories'

urlpatterns = [
    # Public endpoints
    path('', CategoryListView.as_view(), name='category_list'),
    path('all/', AllCategoriesView.as_view(), name='all_categories'),
    path('<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # Admin endpoints
    path('admin/create/', CategoryCreateView.as_view(), name='category_create'),
    path('admin/<slug:slug>/update/', CategoryUpdateView.as_view(), name='category_update'),
    path('admin/<slug:slug>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
]