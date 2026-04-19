"""
users/serializers.py
─────────────────────────────────────────────────────────────────────────────
All user-facing serializers with thorough field-level and object-level validation.

Key improvements over v1:
  • Strong password rules (length, uppercase, digit)
  • Indian phone number normalisation
  • Duplicate email guard on registration
  • Change-password serializer
  • read_only / write_only enforced on every sensitive field
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from core.validators import validate_indian_phone, validate_strong_password
from .models import User


# ─── Registration ─────────────────────────────────────────────────────────────

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new customer account.

    Enforced rules:
      - email     : valid format, must be unique (case-insensitive check)
      - name      : 2-150 characters
      - phone     : valid Indian mobile number (optional but validated if provided)
      - password  : min 8 chars, >=1 uppercase, >=1 digit
      - password2 : must match password
    """
    password  = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Min 8 chars, at least one uppercase letter and one digit.',
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Repeat the same password.',
    )

    class Meta:
        model  = User
        fields = ['email', 'name', 'phone', 'password', 'password2']
        extra_kwargs = {
            'name':  {'min_length': 2, 'max_length': 150},
            'email': {'required': True},
        }

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                'An account with this email address already exists.'
            )
        return normalized

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Name cannot be blank.')
        return cleaned

    def validate_phone(self, value):
        if value:
            return validate_indian_phone(value)
        return value

    def validate_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError(
                {'password2': 'Passwords do not match. Please re-enter your password.'}
            )
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ─── Login ────────────────────────────────────────────────────────────────────

class UserLoginSerializer(serializers.Serializer):
    """Authenticates a user by email + password."""
    email    = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        email    = attrs.get('email', '')
        password = attrs.get('password', '')

        if not email or not password:
            raise serializers.ValidationError('Both email and password are required.')

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError('Invalid email or password. Please try again.')
        if not user.is_active:
            raise serializers.ValidationError(
                'Your account has been deactivated. Please contact support.'
            )
        attrs['user'] = user
        return attrs


# ─── Profile ──────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    """Read/update own profile."""
    class Meta:
        model  = User
        fields = ['id', 'email', 'name', 'phone', 'address', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'email', 'is_staff', 'date_joined']

    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters.')
        return cleaned

    def validate_phone(self, value):
        if value:
            return validate_indian_phone(value)
        return value

    def validate_address(self, value):
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError(
                'Please provide a complete address (at least 10 characters).'
            )
        return value.strip()


# ─── Change Password ──────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    """Verifies the current password before setting the new one."""
    current_password     = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password         = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': 'New passwords do not match.'})
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': 'New password must be different from the current password.'}
            )
        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


# ─── Admin: Full User View ────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    """Read-only serializer for admin user listing."""
    order_count = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'name', 'phone', 'address',
            'is_staff', 'is_active', 'order_count', 'date_joined',
        ]
        read_only_fields = [
            'id', 'email', 'name', 'phone', 'address',
            'is_staff', 'is_active', 'order_count', 'date_joined',
        ]

    def get_order_count(self, obj):
        return obj.orders.count()
