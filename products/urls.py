"""products/urls.py
Admin routes MUST appear BEFORE <slug:slug>/ — otherwise 'admin' matches
as a product slug and returns 404.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public — fixed paths first
    path('',            views.ProductListView.as_view(),      name='product-list'),
    path('featured/',   views.FeaturedProductsView.as_view(), name='featured-products'),
    path('categories/', views.CategoryListView.as_view(),     name='category-list'),

    # Admin — BEFORE <slug:slug>/ catch-all
    path('admin/',                     views.AdminProductListCreateView.as_view(),  name='admin-product-list'),
    path('admin/<int:pk>/',            views.AdminProductDetailView.as_view(),      name='admin-product-detail'),
    path('admin/<int:pk>/stock/',      views.AdminStockUpdateView.as_view(),        name='admin-stock-update'),
    path('admin/categories/',          views.CategoryAdminListCreateView.as_view(), name='admin-category-list'),
    path('admin/categories/<int:pk>/', views.CategoryAdminDetailView.as_view(),     name='admin-category-detail'),

    # Slug catch-all — MUST be last
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
]
