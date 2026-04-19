from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ['name', 'slug', 'icon', 'is_active']
    list_filter         = ['is_active']
    search_fields       = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = ['name', 'category', 'price', 'stock', 'is_featured', 'is_active']
    list_filter         = ['is_featured', 'is_active']
    search_fields       = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
