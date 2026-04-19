"""core/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/',     views.HealthCheckView.as_view(),          name='health-check'),
    path('dashboard/',  views.AdminDashboardStatsView.as_view(),  name='admin-dashboard'),
]
