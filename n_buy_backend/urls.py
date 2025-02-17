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
host = 'n-buy-backend.onrender.com' if settings.DEBUG else 'n-buy-backend.onrender.com'
protocol = 'https' if settings.DEBUG else 'https'

schema_view = get_schema_view(
    openapi.Info(
        title="Buy n Large API",
        default_version='v1',
        description="""
        API para la tienda Buy n Large.
        
        WebSocket Endpoints:
        
        1. Chat WebSocket
        ----------------
        - URL: ws://domain/ws/chat/
        - Descripción: Endpoint WebSocket para la comunicación del chat en tiempo real
        - Autenticación: JWT Token requerido
        - Protocolo: WebSocket sobre HTTP/HTTPS
        
        Mensajes:
        
        a) Autenticación Inicial:
           Request:
           ```json
           {
               "type": "authentication",
               "token": "JWT_TOKEN"
           }
           ```
           
           Response (success):
           ```json
           {
               "type": "authentication_successful",
               "user": "username"
           }
           ```
           
           Response (error):
           ```json
           {
               "type": "error",
               "message": "Invalid token"
           }
           ```
        
        b) Mensaje de Chat:
           Request:
           ```json
           {
               "type": "chat_message",
               "message": "texto del mensaje"
           }
           ```
           
           Response:
           ```json
           {
               "type": "chat_message",
               "message": "respuesta del asistente",
               "is_bot": true,
               "name": "Buy n Large"
           }
           ```
        
        c) Consulta de Ventas:
           - Activada por palabras clave: venta, ventas, vendido, vendidos
           - Timeout: 5 segundos
           - Incluye:
             * Total de ventas
             * Ingresos totales
             * Productos más vendidos
             * Ventas recientes
        
        d) Consulta de Productos:
           - Activada por palabras clave: producto, precio, stock, disponible
           - Incluye:
             * Nombre del producto
             * Precio
             * Disponibilidad
             * Descuentos activos
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@buynlarge.com"),
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
    path('api/', include('recommendations.urls')), 
    path('api/analytics/', include('analytics.urls')),
    
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
