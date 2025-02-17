from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Vista de chat que proporciona la interfaz de usuario
    path('test/', views.chat_test, name='chat_test'),
]

# Documentación de WebSocket
"""
WebSocket Endpoints:

1. Chat WebSocket
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
"""