"""
Lakshmi Crackers — Root URL Configuration
All API routes are versioned under /api/v1/
"""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # API v1
    path('api/v1/', include([
        path('products/', include('products.urls')),
        path('orders/',   include('orders.urls')),
        path('users/',    include('users.urls')),
        path('core/',     include('core.urls')),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
