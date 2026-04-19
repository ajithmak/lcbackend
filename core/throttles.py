"""
core/throttles.py
Custom throttle scopes for sensitive endpoints.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Limits login attempts to 10 per minute per IP address.
    Apply to LoginView with:
        throttle_classes = [LoginRateThrottle]
    """
    scope = 'login'


class OrderPlacementThrottle(AnonRateThrottle):
    """
    Limits order placement to 20 per hour per IP.
    Prevents cart-flooding / inventory abuse.
    """
    scope = 'order_place'


class CouponValidateThrottle(AnonRateThrottle):
    """
    Limits coupon validation attempts to 30 per hour per IP.
    Prevents coupon code brute-force.
    """
    scope = 'coupon_validate'
