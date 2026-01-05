from rest_framework import generics
from .models import Category
from .serializers import CategorySerializer

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True, parent=None)
    serializer_class = CategorySerializer

class AllCategoriesView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
