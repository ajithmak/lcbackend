"""
core/exceptions.py
─────────────────────────────────────────────────────────────────────────────
Centralised exception handling for Lakshmi Crackers API.

All API errors are returned in a consistent envelope:

    {
        "success": false,
        "error": {
            "code":    "PRODUCT_NOT_FOUND",   # machine-readable
            "message": "No product matches the given query.",
            "detail":  { ... }                # optional extra context
        }
    }

Usage in views:
    raise NotFound("Product not found")          # DRF built-in, re-shaped here
    raise ProductOutOfStock(product_name, stock) # custom domain exception
"""

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


# ─── Custom Domain Exceptions ─────────────────────────────────────────────────

class LakshmiBaseException(APIException):
    """Base class for all Lakshmi Crackers domain exceptions."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code  = 'BAD_REQUEST'
    default_detail = 'A request error occurred.'

    def __init__(self, message=None, detail=None):
        self.detail = {
            'code':    self.error_code,
            'message': message or self.default_detail,
            **(({'detail': detail}) if detail else {}),
        }


class ProductOutOfStock(LakshmiBaseException):
    """Raised when a customer tries to order more stock than available."""
    status_code = status.HTTP_409_CONFLICT
    error_code  = 'PRODUCT_OUT_OF_STOCK'
    default_detail = 'Product is out of stock.'

    def __init__(self, product_name: str, available: int):
        super().__init__(
            message=f'"{product_name}" only has {available} unit(s) available.',
            detail={'product_name': product_name, 'available_stock': available},
        )


class ProductNotFound(LakshmiBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code  = 'PRODUCT_NOT_FOUND'
    default_detail = 'Product not found or is no longer available.'


class CouponInvalid(LakshmiBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code  = 'COUPON_INVALID'

    def __init__(self, reason: str):
        super().__init__(message=reason)


class CouponExpired(CouponInvalid):
    error_code = 'COUPON_EXPIRED'

    def __init__(self):
        LakshmiBaseException.__init__(self, message='This coupon has expired.')


class CouponUsageLimitReached(CouponInvalid):
    error_code = 'COUPON_LIMIT_REACHED'

    def __init__(self):
        LakshmiBaseException.__init__(self, message='This coupon has reached its usage limit.')


class CouponMinOrderNotMet(CouponInvalid):
    error_code = 'COUPON_MIN_ORDER'

    def __init__(self, min_value):
        LakshmiBaseException.__init__(
            self,
            message=f'A minimum order of ₹{min_value} is required to use this coupon.',
            detail={'min_order_value': str(min_value)},
        )


class CouponExcludedCategory(CouponInvalid):
    """Coupon cannot be applied — cart contains items from excluded categories."""
    error_code = 'COUPON_EXCLUDED_CATEGORY'

    def __init__(self, category_names=None, excluded_slugs=None):
        cats = ', '.join(category_names) if category_names else 'certain categories'
        msg  = (
            f'This coupon is not valid for items in: {cats}. '
            f'Remove those items from your cart or use a different coupon.'
        )
        LakshmiBaseException.__init__(
            self,
            message=msg,
            detail={
                'excluded_categories': list(category_names or []),
                'excluded_slugs':      list(excluded_slugs  or []),
            },
        )


class OrderEmpty(LakshmiBaseException):
    error_code = 'ORDER_EMPTY'
    default_detail = 'An order must contain at least one item.'


class InvalidOrderStatus(LakshmiBaseException):
    error_code = 'INVALID_ORDER_STATUS'

    def __init__(self, current: str, requested: str):
        super().__init__(
            message=f'Cannot transition order from "{current}" to "{requested}".',
            detail={'current_status': current, 'requested_status': requested},
        )


class AuthenticationFailed(LakshmiBaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code  = 'AUTHENTICATION_FAILED'
    default_detail = 'Invalid credentials provided.'


class PermissionDenied(LakshmiBaseException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code  = 'PERMISSION_DENIED'
    default_detail = 'You do not have permission to perform this action.'


# ─── Central Exception Handler ────────────────────────────────────────────────

def custom_exception_handler(exc, context):
    """
    Replace DRF's default error format with a consistent envelope.

    DRF default:  { "field": ["error message"] }
    Ours:         { "success": false, "error": { "code": "...", "message": "...", "detail": {...} } }
    """
    # Let DRF handle the response object first
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception — return 500
        import logging
        logger = logging.getLogger('django')
        logger.exception('Unhandled exception in view: %s', exc)
        from rest_framework.response import Response
        return Response(
            {
                'success': False,
                'error': {
                    'code':    'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred. Please try again later.',
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Our own domain exceptions already have a shaped .detail dict
    if isinstance(exc, LakshmiBaseException):
        response.data = {
            'success': False,
            'error':   exc.detail,
        }
        return response

    # Re-shape standard DRF errors
    shaped = _shape_drf_errors(response.data, exc)
    response.data = {
        'success': False,
        'error':   shaped,
    }
    return response


def _shape_drf_errors(data, exc) -> dict:
    """
    Convert DRF's varied error formats into our standard error envelope.

    Handles:
      - String errors:        "Authentication credentials were not provided."
      - List errors:          ["This field is required."]
      - Dict field errors:    {"email": ["Enter a valid email address."]}
      - Nested dict errors:   {"items": [{"product_id": ["..."]}]}
    """
    from rest_framework.exceptions import (
        ValidationError, NotAuthenticated, AuthenticationFailed as DRFAuthFailed,
        PermissionDenied as DRFPermDenied, NotFound, MethodNotAllowed,
        Throttled, UnsupportedMediaType,
    )

    # Determine error code from exception type
    code_map = {
        ValidationError:       'VALIDATION_ERROR',
        NotAuthenticated:      'NOT_AUTHENTICATED',
        DRFAuthFailed:         'AUTHENTICATION_FAILED',
        DRFPermDenied:         'PERMISSION_DENIED',
        NotFound:              'NOT_FOUND',
        MethodNotAllowed:      'METHOD_NOT_ALLOWED',
        Throttled:             'RATE_LIMIT_EXCEEDED',
        UnsupportedMediaType:  'UNSUPPORTED_MEDIA_TYPE',
    }
    error_code = 'API_ERROR'
    for exc_class, code in code_map.items():
        if isinstance(exc, exc_class):
            error_code = code
            break

    # Flatten error messages
    if isinstance(data, list):
        message = ' '.join(str(e) for e in data)
        detail  = None
    elif isinstance(data, dict):
        # Field-level validation errors
        detail  = _flatten_dict_errors(data)
        # Compose human-readable summary
        messages = []
        for field, errors in detail.items():
            if field == 'non_field_errors':
                messages.append(errors)
            else:
                messages.append(f'{field}: {errors}')
        message = ' | '.join(messages) if messages else 'Validation failed.'
    else:
        message = str(data)
        detail  = None

    result = {'code': error_code, 'message': message}
    if detail:
        result['detail'] = detail
    return result


def _flatten_dict_errors(errors: dict, prefix: str = '') -> dict:
    """Recursively flatten nested field errors into dot-notation keys."""
    flat = {}
    for key, value in errors.items():
        full_key = f'{prefix}{key}' if not prefix else f'{prefix}.{key}'
        if isinstance(value, dict):
            flat.update(_flatten_dict_errors(value, full_key))
        elif isinstance(value, list):
            # Join list of error strings
            flat[full_key] = ' '.join(str(v) for v in value)
        else:
            flat[full_key] = str(value)
    return flat
