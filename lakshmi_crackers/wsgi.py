"""
WSGI config for Lakshmi Crackers project.
Exposes the WSGI callable as a module-level variable named `application`.
"""
import os

# Load .env file before Django initialises (works with gunicorn too)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; env vars must be set by the host

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lakshmi_crackers.settings')
application = get_wsgi_application()
