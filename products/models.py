"""
products/models.py — Clean PostgreSQL version.

Changes from MongoDB version:
  • Removed d() helper — no longer needed; PostgreSQL returns proper Python Decimal natively
  • is_active   changed SmallIntegerField → BooleanField
  • is_featured changed SmallIntegerField → BooleanField
  • Added db_index=True on frequently-queried fields
  • Added Meta.indexes for composite query optimisation
"""
from decimal import Decimal
from django.db import models


class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=10, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label           = 'products'
        verbose_name        = 'Category'
        verbose_name_plural = 'Categories'
        ordering            = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name           = models.CharField(max_length=200, db_index=True)
    slug           = models.SlugField(unique=True, db_index=True)
    description    = models.TextField(blank=True)
    category       = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products', db_index=True
    )
    price          = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock          = models.PositiveIntegerField(default=0, db_index=True)
    min_order      = models.PositiveIntegerField(default=1)
    image          = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url      = models.URLField(blank=True)
    is_featured    = models.BooleanField(default=False, db_index=True)
    is_active      = models.BooleanField(default=True,  db_index=True)
    unit_type      = models.CharField(
        max_length=20,
        blank=True,
        default='',
        choices=[
            ('box',    'Box'),
            ('pkt',    'Packet'),
            ('piece',  'Piece'),
            ('set',    'Set'),
            ('dozen',  'Dozen'),
            ('bundle', 'Bundle'),
            ('roll',   'Roll'),
        ],
        help_text='Packaging unit shown on the product card (e.g. Box, Packet)',
    )
    tags           = models.CharField(max_length=500, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'products'
        ordering  = ['-created_at']
        indexes   = [
            # Composite: active product listing (most common query)
            models.Index(fields=['is_active', '-created_at'], name='idx_product_active_date'),
            # Composite: featured products widget
            models.Index(fields=['is_active', 'is_featured'], name='idx_product_featured'),
            # Composite: category product count
            models.Index(fields=['category', 'is_active'],    name='idx_product_category_active'),
            # Price range filtering
            models.Index(fields=['price'],                     name='idx_product_price'),
        ]

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        """Percentage off from original price."""
        if self.original_price and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0
