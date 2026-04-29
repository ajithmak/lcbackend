"""
orders/serializers.py — PostgreSQL version.
Decimal fields use Python's native Decimal — no MongoDB Decimal128 workarounds needed.
"""
from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from core.validators import (
    validate_indian_phone,
    validate_address,
    validate_coupon_code,
    validate_discount_value,
    validate_non_negative,
)
from core.exceptions import (
    CouponExpired,
    CouponUsageLimitReached,
    CouponMinOrderNotMet,
    CouponExcludedCategory,
    ProductOutOfStock,
)
from .models import Order, OrderItem, Coupon
from products.models import Product


# ── Coupon Serializer ──────────────────────────────────────────────────────────

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'min_order_value', 'max_uses', 'used_count',
            'is_active', 'valid_from', 'valid_until',
            'excluded_category_slugs',
        ]
        read_only_fields = ['id', 'used_count', 'valid_from']

    def validate_code(self, value):
        return validate_coupon_code(value)

    def validate_min_order_value(self, value):
        if value < Decimal('0'):
            raise serializers.ValidationError('Minimum order value cannot be negative.')
        return value

    def validate_max_uses(self, value):
        if value < 1:
            raise serializers.ValidationError('Max uses must be at least 1.')
        return value

    def validate(self, attrs):
        discount_type  = attrs.get('discount_type',  getattr(self.instance, 'discount_type',  'percent'))
        discount_value = attrs.get('discount_value', getattr(self.instance, 'discount_value', 0))
        validate_discount_value(discount_value, discount_type)

        valid_until = attrs.get('valid_until')
        if valid_until and valid_until <= timezone.now():
            raise serializers.ValidationError({'valid_until': 'Expiry date must be in the future.'})
        return attrs

    def create(self, validated_data):
        validated_data['code'] = validated_data['code'].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'code' in validated_data:
            validated_data['code'] = validated_data['code'].upper()
        # PostgreSQL: super().update() is safe — no [removed-Decimal128] issue
        return super().update(instance, validated_data)


# ── Coupon Validation ──────────────────────────────────────────────────────────

class CouponValidateSerializer(serializers.Serializer):
    code        = serializers.CharField()
    subtotal    = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    # Optional list of product IDs in cart — used to check excluded categories
    product_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        default=list,
    )

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        code        = attrs['code']
        subtotal    = attrs['subtotal']
        product_ids = attrs.get('product_ids', [])

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({'code': 'Coupon code not found.'})

        if not coupon.is_active:
            raise serializers.ValidationError({'code': 'This coupon is no longer active.'})
        if coupon.valid_until and timezone.now() > coupon.valid_until:
            raise CouponExpired()
        if coupon.used_count >= coupon.max_uses:
            raise CouponUsageLimitReached()

        # Check excluded categories — coupon cannot apply if cart has gift boxes or combo packs
        if product_ids:
            blocked = coupon.check_excluded_categories(product_ids)
            if blocked:
                excluded_slugs = coupon.get_excluded_slugs()
                # Build friendly category name list
                cat_names = sorted({cat_name for _, cat_name in blocked})
                raise CouponExcludedCategory(cat_names, excluded_slugs)

        if subtotal < coupon.min_order_value:
            raise CouponMinOrderNotMet(coupon.min_order_value)

        attrs['coupon']   = coupon
        attrs['discount'] = coupon.calculate_discount(subtotal)
        return attrs


# ── Order Item Input ───────────────────────────────────────────────────────────

class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity   = serializers.IntegerField(min_value=1, max_value=1000)


# ── Order Create ───────────────────────────────────────────────────────────────

class OrderCreateSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=150, min_length=2)
    email       = serializers.EmailField()
    phone       = serializers.CharField()
    address     = serializers.CharField()
    items       = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=250)
    coupon_code = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Name is required.')
        return cleaned

    def validate_email(self, value):
        return value.strip().lower()

    def validate_phone(self, value):
        return validate_indian_phone(value)

    def validate_address(self, value):
        return validate_address(value)

    def validate_coupon_code(self, value):
        return value.strip().upper() if value else ''

    def validate_items(self, raw_items):
        validated_items = []
        errors = {}
        for idx, item in enumerate(raw_items):
            s = OrderItemInputSerializer(data=item)
            if not s.is_valid():
                errors[f'items[{idx}]'] = s.errors
            else:
                validated_items.append(s.validated_data)
        if errors:
            raise serializers.ValidationError(errors)

        ids = [i['product_id'] for i in validated_items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Duplicate products in cart.')

        result = []
        for item in validated_items:
            product_id = item['product_id']
            quantity   = item['quantity']
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    f'Product id {product_id} is not available.'
                )
            if not product.is_active:
                raise serializers.ValidationError(
                    f'Product id {product_id} is not available.'
                )
            if product.stock < quantity:
                raise ProductOutOfStock(product.name, product.stock)
            if quantity < product.min_order:
                raise serializers.ValidationError(
                    f'"{product.name}" requires minimum order of {product.min_order}.'
                )
            result.append({'product': product, 'quantity': quantity})
        return result

    def validate(self, attrs):
        items = attrs.get('items', [])
        if not items:
            raise serializers.ValidationError({'items': 'Order must have at least one item.'})

        # d() converts [removed-Decimal128] → Python Decimal before multiplication
        subtotal = sum(
            item['product'].price * item['quantity']
            for item in items
        )

        coupon_code = attrs.get('coupon_code', '').strip().upper()
        coupon      = None
        discount    = Decimal('0.00')

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
            except Coupon.DoesNotExist:
                raise serializers.ValidationError(
                    {'coupon_code': 'Coupon code not found.'}
                )
            if not coupon.is_active:
                raise serializers.ValidationError({'coupon_code': 'Coupon is inactive.'})
            if coupon.valid_until and timezone.now() > coupon.valid_until:
                raise serializers.ValidationError({'coupon_code': 'Coupon has expired.'})
            if coupon.used_count >= coupon.max_uses:
                raise serializers.ValidationError({'coupon_code': 'Coupon usage limit reached.'})

            # Check excluded categories — block coupon if any item is in an excluded category
            product_ids = [item['product'].id for item in items]
            blocked = coupon.check_excluded_categories(product_ids)
            if blocked:
                cat_names = sorted({cat_name for _, cat_name in blocked})
                raise serializers.ValidationError({
                    'coupon_code': (
                        f'This coupon cannot be applied to items in: '
                        f'{", ".join(cat_names)}. '
                        f'Remove those items or use a different coupon.'
                    )
                })

            if subtotal < coupon.min_order_value:
                raise serializers.ValidationError({
                    'coupon_code': (
                        f'Cart total (₹{subtotal:.0f}) is below the '
                        f'₹{coupon.min_order_value:.0f} minimum for this coupon.'
                    )
                })
            discount = coupon.calculate_discount(subtotal)

        attrs['_subtotal'] = subtotal
        attrs['_coupon']   = coupon
        attrs['_discount'] = discount
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items       = validated_data.pop('items')
        coupon_code = validated_data.pop('coupon_code', '')
        subtotal    = validated_data.pop('_subtotal')
        coupon      = validated_data.pop('_coupon')
        discount    = validated_data.pop('_discount')
        user        = self.context.get('user')

        total = max(Decimal('0.00'), subtotal - discount)

        order = Order.objects.create(
            user            = user,
            subtotal        = subtotal,
            discount_amount = discount,
            total           = total,
            coupon          = coupon,
            coupon_code     = coupon_code,
            **validated_data,
        )

        for item in items:
            product  = item['product']
            quantity = item['quantity']
            OrderItem.objects.create(
                order         = order,
                product       = product,
                product_name  = product.name,
                product_price = product.price,
                quantity      = quantity,
            )
            # Update stock in Python (fetch → subtract → save)
            fresh_product       = Product.objects.get(pk=product.pk)
            fresh_product.stock = max(0, fresh_product.stock - quantity)
            fresh_product.save(update_fields=['stock'])

        if coupon:
            # Increment used_count
            fresh_coupon            = Coupon.objects.get(pk=coupon.pk)
            fresh_coupon.used_count = fresh_coupon.used_count + 1
            fresh_coupon.save(update_fields=['used_count'])

        return order


# ── Order Item Output ──────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model        = OrderItem
        fields       = ['id', 'product', 'product_name', 'product_price', 'quantity', 'line_total']
        read_only_fields = fields


# ── Order Detail ───────────────────────────────────────────────────────────────

class OrderDetailSerializer(serializers.ModelSerializer):
    items           = OrderItemSerializer(many=True, read_only=True)
    subtotal        = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total           = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model        = Order
        fields       = [
            'id', 'name', 'email', 'phone', 'address',
            'items', 'subtotal', 'discount_amount', 'total',
            'coupon_code', 'status', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


# ── Order Status Update ────────────────────────────────────────────────────────

_VALID_TRANSITIONS = {
    'pending':    {'confirmed', 'cancelled'},
    'confirmed':  {'processing', 'cancelled'},
    'processing': {'shipped', 'cancelled'},
    'shipped':    {'delivered'},
    'delivered':  set(),
    'cancelled':  set(),
}


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Order
        fields = ['status', 'notes']

    def validate_status(self, new_status):
        instance = self.instance
        if instance is None:
            return new_status
        current = instance.status
        allowed = _VALID_TRANSITIONS.get(current, set())
        if new_status == current:
            return new_status
        if new_status not in allowed:
            from core.exceptions import InvalidOrderStatus
            raise InvalidOrderStatus(current, new_status)
        return new_status

    def update(self, instance, validated_data):
        # PostgreSQL: super().update() is safe — no [removed-Decimal128] issue
        return super().update(instance, validated_data)
