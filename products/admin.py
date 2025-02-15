from django.contrib import admin
from .models import Product, Sale, Inventory, Rating

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'base_price', 'current_price', 'category', 'created_at')
    list_filter = ('brand', 'category')
    search_fields = ('name', 'brand', 'category')
    readonly_fields = ('created_at',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('created_at', 'product')
    search_fields = ('user__email', 'product__name')
    readonly_fields = ('created_at', 'total_price')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('product__name',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'product__name', 'review')