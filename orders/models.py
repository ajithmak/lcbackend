"""
orders/models.py — Clean PostgreSQL version.

Changes from MongoDB version:
  • Removed d() import — not needed with PostgreSQL (returns proper Decimal)
  • is_active changed SmallIntegerField → BooleanField on Coupon
  • OrderItem.save() simplified — no Decimal128 conversion needed
  • Added Meta.indexes for common query patterns
  • Added select_related hints via related_name
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from products.models import Product


class Coupon(models.Model):
    DISCOUNT_TYPES = [('percent', 'Percentage'), ('fixed', 'Fixed Amount')]

    code            = models.CharField(max_length=30, unique=True, db_index=True)
    discount_type   = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent')
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    max_uses        = models.PositiveIntegerField(default=100)
    used_count      = models.PositiveIntegerField(default=0)
    is_active       = models.BooleanField(default=True)
    valid_from      = models.DateTimeField(auto_now_add=True)
    valid_until     = models.DateTimeField(null=True, blank=True)
    # Comma-separated category slugs this coupon CANNOT be applied to
    # Default: gift boxes and combo packs are always excluded
    excluded_category_slugs = models.CharField(
        max_length=500,
        blank=True,
        default='gift-boxes,combo-packs',
        help_text='Comma-separated slugs excluded from this coupon. E.g. gift-boxes,combo-packs',
    )

    class Meta:
        app_label = 'orders'

    def __str__(self):
        return f'{self.code} ({self.discount_type}: {self.discount_value})'

    @property
    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.valid_until and timezone.now() > self.valid_until:
            return False
        return True

    def get_excluded_slugs(self):
        """Return set of excluded category slugs."""
        if not self.excluded_category_slugs:
            return set()
        return {s.strip().lower() for s in self.excluded_category_slugs.split(',') if s.strip()}

    def check_excluded_categories(self, product_ids):
        """
        Check if any of the given product IDs belong to excluded categories.
        Returns list of excluded product names, or empty list if all clear.
        """
        excluded = self.get_excluded_slugs()
        if not excluded:
            return []
        from products.models import Product
        blocked = (
            Product.objects
            .filter(id__in=product_ids, category__slug__in=excluded)
            .select_related('category')
            .values_list('name', 'category__name')
        )
        return list(blocked)

    def calculate_discount(self, subtotal):
        """Calculate discount amount. PostgreSQL returns proper Decimal — no conversion needed."""
        if not self.is_valid:
            return Decimal('0')
        if subtotal < self.min_order_value:
            return Decimal('0')
        if self.discount_type == 'percent':
            return round(subtotal * self.discount_value / 100, 2)
        return min(self.discount_value, subtotal)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
    ]

    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', db_index=True
    )
    name    = models.CharField(max_length=150)
    email   = models.EmailField(db_index=True)
    phone   = models.CharField(max_length=15)
    address = models.TextField()

    subtotal        = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total           = models.DecimalField(max_digits=12, decimal_places=2)

    coupon      = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders'
    )
    coupon_code = models.CharField(max_length=30, blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'orders'
        ordering  = ['-created_at']
        indexes   = [
            models.Index(fields=['status', '-created_at'], name='idx_order_status_date'),
            models.Index(fields=['email'],                  name='idx_order_email'),
        ]

    def __str__(self):
        return f'Order #{self.id} — {self.name} ({self.status})'


class OrderItem(models.Model):
    order         = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product       = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    product_name  = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity      = models.PositiveIntegerField(default=1)
    line_total    = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        app_label = 'orders'

    def save(self, *args, **kwargs):
        # PostgreSQL returns proper Decimal — direct multiplication is safe
        self.line_total = self.product_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'
