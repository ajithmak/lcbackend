"""
products/serializers.py
djongo FIX: boolean fields use integer comparison (=1) not =True.
"""
from decimal import Decimal
from rest_framework import serializers
from django.utils.text import slugify

from core.validators import (
    validate_positive_price,
    validate_non_negative,
    validate_product_name,
    validate_original_price_vs_price,
)
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'description', 'icon',
                  'is_active', 'product_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at', 'product_count']

    def get_product_count(self, obj):
        return Product.objects.filter(category_id=obj.id, is_active=True).count()

    
    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Category name must be at least 2 characters.')
        qs = Category.objects.filter(name__iexact=cleaned)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f'A category named "{cleaned}" already exists.')
        return cleaned

    def validate_icon(self, value):
        return value.strip() if value else ''

    def create(self, validated_data):
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            validated_data['slug'] = slugify(validated_data['name'])
        return super().update(instance, validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    category_name    = serializers.SerializerMethodField()
    category_slug    = serializers.SerializerMethodField()
    discount_percent = serializers.ReadOnlyField()
    in_stock         = serializers.ReadOnlyField()
    # Return full absolute URL so frontend just uses product.image directly
    image            = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug',
            'category', 'category_name', 'category_slug',
            'price', 'original_price', 'discount_percent',
            'stock', 'in_stock', 'min_order',
            'image', 'image_url',
            'is_featured', 'tags', 'unit_type',
        ]

    def get_image(self, obj):
        """Return absolute URL for uploaded image, or None if no image."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        # Fallback: build from MEDIA_URL setting
        from django.conf import settings
        return f"{settings.MEDIA_URL}{obj.image.name}"

    def get_category_name(self, obj):
        try:
            return obj.category.name if obj.category_id else ''
        except Exception:
            return ''

    def get_category_slug(self, obj):
        try:
            return obj.category.slug if obj.category_id else ''
        except Exception:
            return ''


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name    = serializers.SerializerMethodField()
    discount_percent = serializers.ReadOnlyField()
    in_stock         = serializers.ReadOnlyField()
    # Return full absolute URL so frontend just uses product.image directly
    image            = serializers.SerializerMethodField()
    price            = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price   = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    stock     = serializers.IntegerField(min_value=0)
    min_order = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'category', 'category_name',
            'price', 'original_price', 'discount_percent',
            'stock', 'in_stock', 'min_order',
            'image', 'image_url',
            'is_featured', 'is_active', 'tags', 'unit_type',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_image(self, obj):
        """Return absolute URL for uploaded image, or None if no image."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        from django.conf import settings
        return f"{settings.MEDIA_URL}{obj.image.name}"

    def get_category_name(self, obj):
        try:
            return obj.category.name if obj.category_id else ''
        except Exception:
            return ''

    def validate_name(self, value):
        return validate_product_name(value)

    def validate_price(self, value):
        return validate_positive_price(value)

    def validate_original_price(self, value):
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError('Original price must be greater than zero.')
        return value

    def validate_stock(self, value):
        return validate_non_negative(value, 'Stock')

    def validate_is_featured(self, value):
        # FormData sends booleans as strings "true"/"false" — coerce to bool
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def validate_is_active(self, value):
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def validate_image_url(self, value):
        if value and not (value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError('Image URL must start with http:// or https://')
        return value

    def validate_tags(self, value):
        if not value:
            return ''
        parts = [t.strip().lower() for t in value.split(',')]
        return ', '.join(list(dict.fromkeys(t for t in parts if t)))

    def validate(self, attrs):
        price          = attrs.get('price') or (self.instance.price if self.instance else None)
        original_price = attrs.get('original_price')
        if original_price is not None and price is not None:
            try:
                # d() converts [removed-Decimal128] → Python Decimal before comparison
                validate_original_price_vs_price(original_price, price)
            except serializers.ValidationError as e:
                raise serializers.ValidationError(e.detail)

        stock     = attrs.get('stock',     getattr(self.instance, 'stock',     0))
        min_order = attrs.get('min_order', getattr(self.instance, 'min_order', 1))
        if stock is not None and min_order is not None and min_order > stock and stock > 0:
            raise serializers.ValidationError(
                {'min_order': f'Minimum order ({min_order}) cannot exceed stock ({stock}).'}
            )

        # Check category active — Python-level, no ORM boolean filter
        category = attrs.get('category')
        if category:
            try:
                fresh = Category.objects.get(pk=category.pk)
                if not fresh.is_active:
                    raise serializers.ValidationError({'category': 'Category is disabled.'})
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category': 'Category not found.'})
        return attrs

    def _unique_slug(self, name, exclude_pk=None):
        base = slugify(name)
        slug = base
        n    = 1
        while True:
            qs = Product.objects.filter(slug=slug)
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if not qs.exists():
                break
            slug = f'{base}-{n}'
            n   += 1
        return slug

    def create(self, validated_data):
        validated_data['slug'] = self._unique_slug(validated_data['name'])
        # Pull uploaded image from request.FILES — DRF validated_data doesn't carry FILES
        request = self.context.get('request')
        if request and 'image' in request.FILES:
            validated_data['image'] = request.FILES['image']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'name' in validated_data and validated_data['name'] != instance.name:
            validated_data['slug'] = self._unique_slug(
                validated_data['name'], exclude_pk=instance.pk
            )
        # Pull uploaded image from request.FILES — DRF validated_data doesn't carry FILES
        request = self.context.get('request')
        if request and 'image' in request.FILES:
            validated_data['image'] = request.FILES['image']
        return super().update(instance, validated_data)


class StockUpdateSerializer(serializers.Serializer):
    stock = serializers.IntegerField(min_value=0, max_value=100000)

    def validate_stock(self, value):
        return validate_non_negative(value, 'Stock')
