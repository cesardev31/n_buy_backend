from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/metrics/', views.get_dashboard_metrics, name='dashboard_metrics'),
    path('dashboard/sales-history/', views.get_sales_history, name='sales_history'),
    path('dashboard/category-distribution/', views.get_category_distribution, name='category_distribution'),
]
