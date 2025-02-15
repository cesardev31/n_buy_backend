"""
URL configuration for n_buy_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Determinar el host basado en DEBUG
host = 'localhost:8000' if settings.DEBUG else 'n-buy-backend.onrender.com'
protocol = 'http' if settings.DEBUG else 'https'

schema_view = get_schema_view(
    openapi.Info(
        title="N-Buy API",
        default_version='v1',
        description="API para la tienda N-Buy",
        terms_of_service="https://www.n-buy.com/terms/",
        contact=openapi.Contact(email="contact@n-buy.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url=f"{protocol}://{host}",
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticación
    path('accounts/login/', auth_views.LoginView.as_view(template_name='chat/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    
    # Chat
    path('chat/', include('chat.urls', namespace='chat')),
    
    # Swagger URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Redirigir la raíz a Swagger
    path('', lambda request: redirect('schema-swagger-ui'), name='root'),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
