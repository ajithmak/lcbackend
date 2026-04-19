"""
users/models.py — Clean PostgreSQL version.

Changes from MongoDB version:
  • is_active changed SmallIntegerField → BooleanField (Postgres handles this natively)
  • is_staff  changed SmallIntegerField → BooleanField
  • Both were SmallIntegerField only as a djongo workaround (djongo could not
    generate correct SQL for BooleanField). PostgreSQL handles BooleanField perfectly.
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',     True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active',    True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email       = models.EmailField(unique=True, db_index=True)
    name        = models.CharField(max_length=150)
    phone       = models.CharField(max_length=15, blank=True)
    address     = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)   # restored — Postgres supports this natively
    is_staff    = models.BooleanField(default=False)  # restored — no [removed-djongo] workaround needed
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        app_label           = 'users'
        verbose_name        = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.name} <{self.email}>'
