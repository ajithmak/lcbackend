"""
users/views.py
─────────────────────────────────────────────────────────────────────────────
Authentication and profile management views.

Improvements over v1:
  • All responses use the standard success envelope via SuccessResponseMixin
  • Change-password endpoint added
  • Admin user listing now uses IsAdminUser permission (not a manual check)
  • Proper 404 handling via get_object_or_404
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken

from core.mixins import SuccessResponseMixin, PaginatedResponseMixin
from core.throttles import LoginRateThrottle

from .models import User
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    AdminUserSerializer,
)

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Generate JWT access + refresh token pair."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


# ─── Public Auth Views ────────────────────────────────────────────────────────

class RegisterView(SuccessResponseMixin, APIView):
    """
    POST /api/v1/users/register/
    Create a new customer account and return JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user   = serializer.save()
        tokens = get_tokens_for_user(user)
        logger.info('New user registered: %s', user.email)

        return self.created(
            data={
                'tokens': tokens,
                'user': UserProfileSerializer(user).data,
            },
            message='Account created successfully. Welcome to Lakshmi Crackers!',
        )


class LoginView(SuccessResponseMixin, APIView):
    """
    POST /api/v1/users/login/
    Authenticate and receive JWT access + refresh tokens.
    Rate-limited to 10 attempts/minute per IP.
    """
    permission_classes = [AllowAny]
    throttle_classes   = [LoginRateThrottle]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user   = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        logger.info('User logged in: %s', user.email)

        return self.ok(
            data={
                'tokens': tokens,
                'user':   UserProfileSerializer(user).data,
            },
            message='Login successful.',
        )


# ─── Authenticated User Views ─────────────────────────────────────────────────

class ProfileView(SuccessResponseMixin, generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/users/profile/   — retrieve own profile
    PATCH /api/v1/users/profile/   — update name, phone, address
    """
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.ok(serializer.data)

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop('partial', False)
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self.ok(serializer.data, message='Profile updated successfully.')


class ChangePasswordView(SuccessResponseMixin, APIView):
    """
    PATCH /api/v1/users/password/change/
    Requires current password. Invalidates existing refresh tokens on success.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info('Password changed for user: %s', request.user.email)
        return self.ok(message='Password changed successfully. Please log in again.')


# ─── Admin Views ──────────────────────────────────────────────────────────────

class AdminUserListView(PaginatedResponseMixin, generics.ListAPIView):
    """
    GET /api/v1/users/admin/list/
    Admin-only: paginated list of all registered users.
    """
    serializer_class   = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset           = User.objects.all().order_by('-date_joined')
