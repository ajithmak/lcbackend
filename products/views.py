"""
products/views.py — PostgreSQL version.
BooleanField filters use True/False directly — standard Django ORM.
"""
import logging
from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from core.mixins import SuccessResponseMixin, PaginatedResponseMixin
from core.exceptions import ProductNotFound

from .models import Product, Category
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    CategorySerializer,
    StockUpdateSerializer,
)

logger = logging.getLogger(__name__)


def _parse_price(request, param):
    from rest_framework.exceptions import ValidationError
    raw = request.query_params.get(param)
    if raw is None:
        return None
    try:
        val = float(raw)
        if val < 0:
            raise ValueError
        return val
    except ValueError:
        raise ValidationError({param: f'"{raw}" is not a valid price.'})


# ── Category views ─────────────────────────────────────────────────────────────

class CategoryListView(PaginatedResponseMixin, generics.ListAPIView):
    serializer_class   = CategorySerializer
    permission_classes = [AllowAny]
    queryset           = Category.objects.filter(is_active=True)


class CategoryAdminListCreateView(
    SuccessResponseMixin, PaginatedResponseMixin, generics.ListCreateAPIView
):
    serializer_class   = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset           = Category.objects.all().order_by('name')

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        cat = s.save()
        logger.info('Admin %s created category: %s', request.user.email, cat.name)
        return self.created(s.data, message=f'Category "{cat.name}" created.')


class CategoryAdminDetailView(
    SuccessResponseMixin, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class   = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset           = Category.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        obj     = self.get_object()
        s       = self.get_serializer(obj, data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        cat = s.save()
        return self.ok(s.data, message=f'Category "{cat.name}" updated.')

    def destroy(self, request, *args, **kwargs):
        obj   = self.get_object()
        count = Product.objects.filter(category_id=obj.id, is_active=True).count()
        if count > 0:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f'Cannot delete "{obj.name}": {count} active product(s) assigned.'
            )
        name = obj.name
        obj.delete()
        logger.info('Admin %s deleted category: %s', request.user.email, name)
        return self.deleted(f'Category "{name}" deleted.')


# ── Public product views ────────────────────────────────────────────────────────

class ProductListView(PaginatedResponseMixin, generics.ListAPIView):
    """GET /api/v1/products/ — with filters"""
    serializer_class   = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'description', 'tags']
    ordering_fields    = ['price', 'name', 'created_at', 'stock']
    ordering           = ['-created_at']

    def get_queryset(self):
        # SmallIntegerField: filter([removed-is_active=1]) → WHERE "is_active" = 1  ✓
        qs = Product.objects.filter(is_active=True)

        # Category: separate single-table query, Python is_active check (no JOIN)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            try:
                cat = Category.objects.get(slug=category_slug)
                if not cat.is_active:
                    return Product.objects.none()
                qs = qs.filter(category_id=cat.id)
            except Category.DoesNotExist:
                return Product.objects.none()

        min_price = _parse_price(self.request, 'min_price')
        max_price = _parse_price(self.request, 'max_price')
        if min_price is not None and max_price is not None and min_price > max_price:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'min_price': 'min_price cannot exceed max_price.'})
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        if self.request.query_params.get('featured') == 'true':
            qs = qs.filter(is_featured=True)
        if self.request.query_params.get('in_stock') == 'true':
            qs = qs.filter(stock__gt=0)

        return qs


class ProductDetailView(SuccessResponseMixin, APIView):
    """GET /api/v1/products/<slug>/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
            if not product.is_active:
                raise Product.DoesNotExist
        except Product.DoesNotExist:
            raise ProductNotFound(f'No product found with slug "{slug}".')
        # Pass request context so get_image() can build absolute URLs
        return self.ok(ProductDetailSerializer(product, context={'request': request}).data)


class FeaturedProductsView(PaginatedResponseMixin, generics.ListAPIView):
    """GET /api/v1/products/featured/"""
    serializer_class   = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True, is_featured=True, stock__gt=0)
            .order_by('-created_at')
        )


# ── Admin product views ─────────────────────────────────────────────────────────

class AdminProductListCreateView(
    SuccessResponseMixin, PaginatedResponseMixin, generics.ListCreateAPIView
):
    serializer_class   = ProductDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]  # accept file uploads
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'description']
    ordering_fields    = ['price', 'stock', 'created_at', 'name']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = Product.objects.all()
        p  = self.request.query_params.get('is_active')
        if p == 'true':
            qs = qs.filter(is_active=True)
        elif p == 'false':
            qs = qs.filter(is_active=False)
        cat_name = self.request.query_params.get('category_name')
        if cat_name:
            cat_ids = list(
                Category.objects.filter(name__icontains=cat_name)
                .values_list('id', flat=True)
            )
            return qs.filter(category_id__in=cat_ids) if cat_ids else Product.objects.none()
        return qs

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        product = s.save()
        logger.info('Admin %s created product: %s', request.user.email, product.name)
        return self.created(s.data, message=f'Product "{product.name}" created.')


class AdminProductDetailView(
    SuccessResponseMixin, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class   = ProductDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]  # accept file uploads
    queryset           = Product.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        obj     = self.get_object()
        s       = self.get_serializer(obj, data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        product = s.save()
        logger.info('Admin %s updated product id=%s', request.user.email, product.id)
        return self.ok(s.data, message=f'Product "{product.name}" updated.')

    def destroy(self, request, *args, **kwargs):
        obj           = self.get_object()
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        logger.info('Admin %s deactivated product id=%s', request.user.email, obj.id)
        return self.deleted(f'Product "{obj.name}" deactivated.')


class AdminStockUpdateView(SuccessResponseMixin, APIView):
    """PATCH /api/v1/products/admin/<pk>/stock/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        s       = StockUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        old           = product.stock
        product.stock = s.validated_data['stock']
        product.save(update_fields=['stock', 'updated_at'])
        logger.info('Admin %s stock id=%s: %s→%s', request.user.email, pk, old, product.stock)
        return self.ok(
            data={'id': product.id, 'name': product.name, 'stock': product.stock},
            message=f'Stock updated to {product.stock} units.',
        )
