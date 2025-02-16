from django.contrib import admin
from .models import Product, Sale, Inventory, Rating

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'base_price', 'current_price', 'category', 'created_at')
    list_filter = ('brand', 'category')
    search_fields = ('name', 'brand', 'description')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('product__brand', 'product__category')
    search_fields = ('product__name',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'last_updated')
    list_filter = ('product__brand', 'product__category')
    search_fields = ('product__name',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'score', 'created_at')
    list_filter = ('score', 'product__brand', 'product__category')
    search_fields = ('user__email', 'product__name', 'review')