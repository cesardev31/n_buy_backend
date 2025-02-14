from django.contrib import admin
from .models import Producto, Inventory, Rating

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'category')
    search_fields = ('name', 'brand')
    list_filter = ('category',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'last_updated')
    search_fields = ('product__name',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    search_fields = ('user__username', 'product__name')