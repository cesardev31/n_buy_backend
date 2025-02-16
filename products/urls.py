from django.urls import path
from . import views

urlpatterns = [
    # Products
    path('', views.get_products, name='get_products'),
    path('<int:product_id>', views.get_product_by_id, name='get_product_by_id'),
    path('create/', views.create_product, name='create_product'),
    path('update/<int:product_id>/', views.update_product, name='update_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    
    # Inventory
    path('inventory/', views.get_inventory, name='get_inventory'),
    path('inventory/create/', views.create_inventory, name='create_inventory'),
    path('inventory/<int:product_id>/', views.get_inventory, name='get_product_inventory'),
    
    # Ratings
    path('ratings/create/', views.create_rating, name='create_rating'),
    path('ratings/<int:product_id>/', views.get_product_ratings, name='get_product_ratings'),
    
    # Sales
    path('sales/create/', views.create_sale, name='create_sale'),
    path('sales/', views.get_sales, name='get_sales'),
] 