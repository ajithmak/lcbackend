"""users/urls.py"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/',          views.RegisterView.as_view(),       name='user-register'),
    path('login/',             views.LoginView.as_view(),          name='user-login'),
    path('token/refresh/',     TokenRefreshView.as_view(),         name='token-refresh'),
    path('profile/',           views.ProfileView.as_view(),        name='user-profile'),
    path('password/change/',   views.ChangePasswordView.as_view(), name='change-password'),
    path('admin/list/',        views.AdminUserListView.as_view(),  name='admin-user-list'),
]
