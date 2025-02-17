from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

@login_required
def chat_test(request):
    """
    Vista para cargar la interfaz de chat.
    
    Esta vista renderiza la página de chat que permite a los usuarios:
    - Conectarse al WebSocket para comunicación en tiempo real
    - Enviar y recibir mensajes
    - Consultar información sobre ventas y productos
    - Recibir respuestas del asistente AI
    
    WebSocket Endpoints:
    - Conexión: ws://domain/ws/chat/
    - Autenticación: Requiere token JWT
    
    Funcionalidades:
    - Autenticación mediante JWT
    - Procesamiento de mensajes con AI
    - Consulta de datos de ventas y productos
    - Manejo de errores y timeouts
    - Formato de moneda y fechas
    """
    return render(request, 'chat/test.html')