"""
tests/test_validation.py
─────────────────────────────────────────────────────────────────────────────
Unit tests for all custom validators, serializers, and exception handling.

Run with:
    python manage.py test tests
    # or with coverage:
    coverage run manage.py test tests && coverage report
"""

from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from core.validators import (
    validate_indian_phone,
    validate_strong_password,
    validate_positive_price,
    validate_non_negative,
    validate_coupon_code,
    validate_address,
    validate_original_price_vs_price,
)
from core.exceptions import (
    ProductOutOfStock,
    CouponExpired,
    CouponUsageLimitReached,
    CouponMinOrderNotMet,
    InvalidOrderStatus,
)
from rest_framework import serializers


# ─── Validator Unit Tests ─────────────────────────────────────────────────────

class PhoneValidatorTests(TestCase):

    def _ok(self, value, expected):
        self.assertEqual(validate_indian_phone(value), expected)

    def _fail(self, value):
        with self.assertRaises(serializers.ValidationError):
            validate_indian_phone(value)

    def test_plain_10_digit(self):
        self._ok('9876543210', '9876543210')

    def test_with_country_code_plus(self):
        self._ok('+919876543210', '9876543210')

    def test_with_country_code_no_plus(self):
        self._ok('919876543210', '9876543210')

    def test_with_leading_zero(self):
        self._ok('09876543210', '9876543210')

    def test_with_spaces(self):
        self._ok('98765 43210', '9876543210')

    def test_starts_with_6(self):
        self._ok('6123456789', '6123456789')

    def test_starts_with_5_invalid(self):
        self._fail('5123456789')

    def test_too_short(self):
        self._fail('987654321')

    def test_too_long(self):
        self._fail('98765432109')

    def test_all_zeros_invalid(self):
        self._fail('0000000000')


class PasswordValidatorTests(TestCase):

    def _ok(self, value):
        self.assertEqual(validate_strong_password(value), value)

    def _fail(self, value):
        with self.assertRaises(serializers.ValidationError):
            validate_strong_password(value)

    def test_valid_password(self):
        self._ok('Abcdef12')

    def test_too_short(self):
        self._fail('Ab1')

    def test_no_uppercase(self):
        self._fail('abcdefg1')

    def test_no_digit(self):
        self._fail('Abcdefgh')

    def test_exactly_8_chars(self):
        self._ok('Abcdef12')

    def test_long_password(self):
        self._ok('MyStrongPassword123!')


class PriceValidatorTests(TestCase):

    def test_valid_price(self):
        self.assertEqual(validate_positive_price('150.00'), Decimal('150.00'))

    def test_zero_price_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_positive_price(0)

    def test_negative_price_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_positive_price(-10)

    def test_exceeds_max_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_positive_price(9999999)

    def test_decimal_string_input(self):
        result = validate_positive_price('99.99')
        self.assertEqual(result, Decimal('99.99'))


class StockValidatorTests(TestCase):

    def test_zero_is_valid(self):
        self.assertEqual(validate_non_negative(0, 'Stock'), 0)

    def test_positive_is_valid(self):
        self.assertEqual(validate_non_negative(100, 'Stock'), 100)

    def test_negative_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_non_negative(-1, 'Stock')

    def test_string_number_parsed(self):
        self.assertEqual(validate_non_negative('50', 'Stock'), 50)

    def test_float_string_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_non_negative('abc', 'Stock')


class CouponCodeValidatorTests(TestCase):

    def test_valid_code(self):
        self.assertEqual(validate_coupon_code('DIWALI10'), 'DIWALI10')

    def test_lowercase_uppercased(self):
        self.assertEqual(validate_coupon_code('diwali10'), 'DIWALI10')

    def test_too_short_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_coupon_code('AB')

    def test_too_long_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_coupon_code('A' * 21)

    def test_special_chars_fail(self):
        with self.assertRaises(serializers.ValidationError):
            validate_coupon_code('SAVE-50')

    def test_underscore_allowed(self):
        self.assertEqual(validate_coupon_code('SAVE_50'), 'SAVE_50')


class AddressValidatorTests(TestCase):

    def test_valid_address(self):
        addr = '12 Main Street, Chennai, Tamil Nadu'
        self.assertEqual(validate_address(addr), addr)

    def test_too_short_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_address('Chennai')

    def test_exactly_10_chars_ok(self):
        self.assertEqual(validate_address('1234567890'), '1234567890')


class OriginalPriceValidatorTests(TestCase):

    def test_original_greater_than_price(self):
        # Should not raise
        validate_original_price_vs_price(Decimal('200'), Decimal('150'))

    def test_original_equal_to_price_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_original_price_vs_price(Decimal('150'), Decimal('150'))

    def test_original_less_than_price_fails(self):
        with self.assertRaises(serializers.ValidationError):
            validate_original_price_vs_price(Decimal('100'), Decimal('150'))

    def test_none_original_price_ok(self):
        # Should not raise — original_price is optional
        validate_original_price_vs_price(None, Decimal('150'))


# ─── Domain Exception Tests ───────────────────────────────────────────────────

class DomainExceptionTests(TestCase):

    def test_product_out_of_stock_shape(self):
        exc = ProductOutOfStock('Gold Sparklers', 3)
        self.assertEqual(exc.detail['code'], 'PRODUCT_OUT_OF_STOCK')
        self.assertIn('Gold Sparklers', exc.detail['message'])
        self.assertEqual(exc.detail['detail']['available_stock'], 3)
        self.assertEqual(exc.status_code, 409)

    def test_coupon_expired_shape(self):
        exc = CouponExpired()
        self.assertEqual(exc.detail['code'], 'COUPON_EXPIRED')
        self.assertIn('expired', exc.detail['message'])

    def test_coupon_limit_shape(self):
        exc = CouponUsageLimitReached()
        self.assertEqual(exc.detail['code'], 'COUPON_LIMIT_REACHED')

    def test_coupon_min_order_shape(self):
        exc = CouponMinOrderNotMet(Decimal('500'))
        self.assertEqual(exc.detail['code'], 'COUPON_MIN_ORDER')
        self.assertIn('500', exc.detail['message'])
        self.assertEqual(exc.detail['detail']['min_order_value'], '500')

    def test_invalid_order_status_shape(self):
        exc = InvalidOrderStatus('delivered', 'pending')
        self.assertEqual(exc.detail['code'], 'INVALID_ORDER_STATUS')
        self.assertIn('delivered', exc.detail['message'])
        self.assertEqual(exc.detail['detail']['current_status'], 'delivered')


# ─── API Integration Tests ────────────────────────────────────────────────────

class UserRegistrationAPITests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.url    = '/api/v1/users/register/'

    def _post(self, data):
        return self.client.post(self.url, data, format='json')

    def test_successful_registration(self):
        res = self._post({
            'email':     'test@example.com',
            'name':      'Test User',
            'phone':     '9876543210',
            'password':  'SecurePass1',
            'password2': 'SecurePass1',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertIn('tokens', res.data['data'])
        self.assertIn('user',   res.data['data'])

    def test_duplicate_email_rejected(self):
        self._post({
            'email': 'dup@example.com', 'name': 'A',
            'password': 'SecurePass1', 'password2': 'SecurePass1',
        })
        res = self._post({
            'email': 'dup@example.com', 'name': 'B',
            'password': 'SecurePass1', 'password2': 'SecurePass1',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_password_mismatch_rejected(self):
        res = self._post({
            'email': 'x@example.com', 'name': 'X',
            'password': 'SecurePass1', 'password2': 'DifferentPass1',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        res = self._post({
            'email': 'y@example.com', 'name': 'Y',
            'password': 'weak', 'password2': 'weak',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_phone_rejected(self):
        res = self._post({
            'email': 'z@example.com', 'name': 'Z',
            'phone': '1234567890',    # starts with 1 — invalid Indian number
            'password': 'SecurePass1', 'password2': 'SecurePass1',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class CouponValidationAPITests(APITestCase):

    def setUp(self):
        from orders.models import Coupon
        self.client = APIClient()
        self.url    = '/api/v1/orders/coupon/validate/'
        self.coupon = Coupon.objects.create(
            code='TESTCODE',
            discount_type='percent',
            discount_value=Decimal('10'),
            min_order_value=Decimal('500'),
            max_uses=100,
            is_active=True,
        )

    def test_valid_coupon(self):
        res = self.client.post(self.url, {'code': 'TESTCODE', 'subtotal': '600.00'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['data']['code'], 'TESTCODE')
        self.assertEqual(res.data['data']['discount'], '60.00')

    def test_invalid_code(self):
        res = self.client.post(self.url, {'code': 'NOSUCHCODE', 'subtotal': '600.00'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_min_order_not_met(self):
        res = self.client.post(self.url, {'code': 'TESTCODE', 'subtotal': '200.00'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(res.data['error']['code'], 'COUPON_MIN_ORDER')

    def test_inactive_coupon(self):
        self.coupon.is_active = False
        self.coupon.save()
        res = self.client.post(self.url, {'code': 'TESTCODE', 'subtotal': '600.00'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exhausted_coupon(self):
        self.coupon.used_count = 100
        self.coupon.save()
        res = self.client.post(self.url, {'code': 'TESTCODE', 'subtotal': '600.00'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(res.data['error']['code'], 'COUPON_LIMIT_REACHED')


class OrderStatusTransitionTests(APITestCase):
    """Test that invalid status transitions are rejected."""

    def setUp(self):
        from users.models import User
        from orders.models import Order
        self.admin = User.objects.create_superuser(
            email='admin@test.com', password='AdminPass1', name='Admin'
        )
        self.client.force_authenticate(user=self.admin)
        self.order = Order.objects.create(
            name='Test', email='t@t.com', phone='9000000000',
            address='123 Test Street, Chennai',
            subtotal=Decimal('500'), total=Decimal('500'),
            status='delivered',
        )

    def test_cannot_move_delivered_to_pending(self):
        res = self.client.patch(
            f'/api/v1/orders/admin/{self.order.id}/',
            {'status': 'pending'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error']['code'], 'INVALID_ORDER_STATUS')

    def test_can_stay_delivered(self):
        res = self.client.patch(
            f'/api/v1/orders/admin/{self.order.id}/',
            {'status': 'delivered'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
