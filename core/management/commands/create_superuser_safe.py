"""
core/management/commands/create_superuser_safe.py

Creates a superuser from environment variables.
Safe to run on every deploy — skips silently if user already exists.

Usage in Render Build Command:
  python manage.py create_superuser_safe

Required environment variables:
  DJANGO_SUPERUSER_EMAIL
  DJANGO_SUPERUSER_PASSWORD
  DJANGO_SUPERUSER_NAME   (optional, defaults to "Admin")
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create superuser from env vars — safe to run multiple times'

    def handle(self, *args, **kwargs):
        User  = get_user_model()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        pwd   = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '').strip()
        name  = os.environ.get('DJANGO_SUPERUSER_NAME', 'Admin').strip()

        if not email or not pwd:
            self.stdout.write(self.style.WARNING(
                'Skipping superuser creation — '
                'DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD not set.'
            ))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f'Superuser "{email}" already exists — skipping.'
            ))
            return

        User.objects.create_superuser(email=email, password=pwd, name=name)
        self.stdout.write(self.style.SUCCESS(
            f'Superuser "{email}" created successfully.'
        ))
