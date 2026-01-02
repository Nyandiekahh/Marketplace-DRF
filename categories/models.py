"""
Models for the categories app.
"""

from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Model for product/service categories.
    Supports hierarchical structure with parent-child relationships.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Category Name'
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name='URL Slug'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='Parent Category'
    )
    icon = models.ImageField(
        upload_to='category_icons/',
        null=True,
        blank=True,
        verbose_name='Category Icon'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Display Order',
        help_text='Lower numbers appear first'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        """String representation showing hierarchy."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate slug if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def ad_count(self):
        """Return count of active ads in this category."""
        return self.ads.filter(status='active').count()
    
    def get_all_subcategories(self):
        """Recursively get all subcategories."""
        subcats = list(self.subcategories.all())
        for subcat in list(subcats):
            subcats.extend(subcat.get_all_subcategories())
        return subcats
    
    def get_breadcrumb(self):
        """Get breadcrumb trail for this category."""
        breadcrumb = [self]
        parent = self.parent
        while parent:
            breadcrumb.insert(0, parent)
            parent = parent.parent
        return breadcrumb