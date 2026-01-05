from django.urls import path
from . import views

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='category-list'),
    path('all/', views.AllCategoriesView.as_view(), name='all-categories'),
    path('<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
]
