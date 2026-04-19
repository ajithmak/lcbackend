"""
core/validators.py
─────────────────────────────────────────────────────────────────────────────
Reusable field-level validators shared across users, products, and orders apps.
Each validator raises serializers.ValidationError with a clear message.
"""

import re
from decimal import Decimal
from rest_framework import serializers


# ─── Phone ────────────────────────────────────────────────────────────────────

def validate_indian_phone(value: str) -> str:
    """
    Accept Indian mobile numbers in these formats:
        9876543210          (10 digits starting with 6-9)
        +919876543210       (with country code)
        0 9876543210        (with leading 0)
    Returns the normalised 10-digit number.
    """
    cleaned = re.sub(r'[\s\-\(\)]', '', str(value))

    # Strip country code
    if cleaned.startswith('+91'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith('0') and len(cleaned) == 11:
        cleaned = cleaned[1:]

    if not re.fullmatch(r'[6-9]\d{9}', cleaned):
        raise serializers.ValidationError(
            'Enter a valid 10-digit Indian mobile number (must start with 6, 7, 8, or 9).'
        )
    return cleaned


# ─── Password ─────────────────────────────────────────────────────────────────

def validate_strong_password(value: str) -> str:
    """
    Password must be:
      - At least 8 characters long
      - Contain at least one uppercase letter
      - Contain at least one digit
    """
    if len(value) < 8:
        raise serializers.ValidationError('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', value):
        raise serializers.ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'\d', value):
        raise serializers.ValidationError('Password must contain at least one digit.')
    return value


# ─── Pricing ──────────────────────────────────────────────────────────────────

def validate_positive_price(value) -> Decimal:
    """Price must be a positive non-zero number."""
    if value is None:
        raise serializers.ValidationError('Price is required.')
    try:
        dec = Decimal(str(value))
    except Exception:
        raise serializers.ValidationError('Enter a valid price.')
    if dec <= 0:
        raise serializers.ValidationError('Price must be greater than ₹0.')
    if dec > Decimal('999999.99'):
        raise serializers.ValidationError('Price cannot exceed ₹9,99,999.')
    return dec


def validate_non_negative(value, field_name: str = 'Value') -> int:
    """Generic non-negative integer validator (for stock, min_order, etc.)."""
    try:
        val = int(value)
    except (TypeError, ValueError):
        raise serializers.ValidationError(f'{field_name} must be a whole number.')
    if val < 0:
        raise serializers.ValidationError(f'{field_name} cannot be negative.')
    return val


def validate_discount_value(value, discount_type: str) -> Decimal:
    """
    Percentage: 0 < value <= 100
    Fixed:      value > 0
    """
    try:
        dec = Decimal(str(value))
    except Exception:
        raise serializers.ValidationError('Enter a valid discount value.')
    if dec <= 0:
        raise serializers.ValidationError('Discount value must be greater than 0.')
    if discount_type == 'percent' and dec > 100:
        raise serializers.ValidationError('Percentage discount cannot exceed 100%.')
    return dec


# ─── Text ─────────────────────────────────────────────────────────────────────

def validate_non_empty_string(value: str, field_name: str = 'Field') -> str:
    """Strip whitespace and reject empty strings."""
    cleaned = str(value).strip()
    if not cleaned:
        raise serializers.ValidationError(f'{field_name} cannot be blank.')
    return cleaned


def validate_coupon_code(value: str) -> str:
    """
    Coupon codes: 3–20 alphanumeric + underscore characters, uppercased.
    """
    cleaned = str(value).strip().upper()
    if not re.fullmatch(r'[A-Z0-9_]{3,20}', cleaned):
        raise serializers.ValidationError(
            'Coupon code must be 3–20 characters long and contain only letters, digits, or underscores.'
        )
    return cleaned


def validate_product_name(value: str) -> str:
    """Product name: 3–200 characters, not all numbers/special chars."""
    cleaned = str(value).strip()
    if len(cleaned) < 3:
        raise serializers.ValidationError('Product name must be at least 3 characters long.')
    if len(cleaned) > 200:
        raise serializers.ValidationError('Product name cannot exceed 200 characters.')
    if re.fullmatch(r'[\d\W]+', cleaned):
        raise serializers.ValidationError('Product name must contain at least some letters.')
    return cleaned


def validate_address(value: str) -> str:
    """Address must be at least 10 characters."""
    cleaned = str(value).strip()
    if len(cleaned) < 10:
        raise serializers.ValidationError(
            'Please provide a complete delivery address (minimum 10 characters).'
        )
    return cleaned


def validate_original_price_vs_price(original_price, price) -> None:
    """
    If original_price is provided, it must be strictly greater than price.
    Raises serializers.ValidationError otherwise.
    """
    if original_price is None:
        return
    try:
        op = Decimal(str(original_price))
        p  = Decimal(str(price))
    except Exception:
        return
    if op <= p:
        raise serializers.ValidationError(
            {'original_price': 'Original price must be greater than the selling price.'}
        )


# ─── Cart / Order Items ───────────────────────────────────────────────────────

def validate_order_items(items: list) -> list:
    """
    Deep-validate the items list submitted by the client.
    Each element must be: { product_id: int (>0), quantity: int (>0) }
    Returns the cleaned list with integer values.
    """
    if not items:
        raise serializers.ValidationError('Order must contain at least one item.')
    if len(items) > 50:
        raise serializers.ValidationError('An order cannot contain more than 50 different products.')

    seen_ids = set()
    cleaned  = []
    for idx, item in enumerate(items):
        prefix = f'items[{idx}]'

        # product_id
        try:
            product_id = int(item['product_id'])
            if product_id <= 0:
                raise ValueError
        except (KeyError, TypeError):
            raise serializers.ValidationError(f'{prefix}: "product_id" is required.')
        except ValueError:
            raise serializers.ValidationError(f'{prefix}: "product_id" must be a positive integer.')

        # quantity
        try:
            quantity = int(item['quantity'])
            if quantity <= 0:
                raise ValueError
        except (KeyError, TypeError):
            raise serializers.ValidationError(f'{prefix}: "quantity" is required.')
        except ValueError:
            raise serializers.ValidationError(f'{prefix}: "quantity" must be a positive integer.')

        # Max per-item quantity sanity check
        if quantity > 1000:
            raise serializers.ValidationError(
                f'{prefix}: quantity cannot exceed 1000 per product.'
            )

        # Duplicate product
        if product_id in seen_ids:
            raise serializers.ValidationError(
                f'{prefix}: product {product_id} appears more than once. Combine quantities instead.'
            )
        seen_ids.add(product_id)
        cleaned.append({'product_id': product_id, 'quantity': quantity})

    return cleaned
