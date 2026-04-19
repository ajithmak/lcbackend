"""orders/urls.py
Sub-resources (admin/coupons/) placed BEFORE pk catch-all (admin/<int:pk>/).
Public <int:pk>/ is last.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('place/',           views.PlaceOrderView.as_view(),     name='place-order'),
    path('coupon/validate/', views.ValidateCouponView.as_view(), name='validate-coupon'),
    path('my/',              views.MyOrdersView.as_view(),       name='my-orders'),

    # Admin — sub-resources BEFORE pk catch-all
    path('admin/',                  views.AdminOrderListView.as_view(),        name='admin-order-list'),
    path('admin/coupons/',          views.AdminCouponListCreateView.as_view(), name='admin-coupon-list'),
    path('admin/coupons/<int:pk>/', views.AdminCouponDetailView.as_view(),     name='admin-coupon-detail'),
    path('admin/<int:pk>/',         views.AdminOrderUpdateView.as_view(),      name='admin-order-detail'),

    # Public pk catch-all — last
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
]
