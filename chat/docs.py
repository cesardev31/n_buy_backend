from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

@swagger_auto_schema(
    method='get',
    operation_description="""
    WebSocket Chat Documentation

    Este endpoint proporciona documentación sobre cómo conectarse y usar el chat WebSocket.

    WebSocket URL: `ws://your-domain/ws/chat/`

    Mensajes del Cliente al Servidor:
    ```json
    {
        "message": "string",    // El mensaje que deseas enviar al bot
        "name": "string",       // Nombre del usuario (opcional, default: "Usuario")
        "is_admin": boolean     // Si el usuario es administrador (opcional, default: false)
    }
    ```

    Mensajes del Servidor al Cliente:
    ```json
    {
        "message": "string",     // El mensaje de respuesta
        "is_bot": boolean,       // true si es un mensaje del bot, false si es del usuario
        "is_typing": boolean,    // true cuando el bot está "escribiendo"
        "name": "string",        // Nombre del remitente (Bot o nombre del usuario)
        "is_admin": boolean      // Si el remitente es administrador
    }
    ```

    Ejemplo de uso con JavaScript:
    ```javascript
    const socket = new WebSocket('ws://your-domain/ws/chat/');

    // Manejar la conexión
    socket.onopen = function(e) {
        console.log('Conexión establecida');
    };

    // Enviar un mensaje
    function sendMessage(message, name = 'Usuario', isAdmin = false) {
        socket.send(JSON.stringify({
            'message': message,
            'name': name,
            'is_admin': isAdmin
        }));
    }

    // Recibir mensajes
    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        if (data.is_typing) {
            // Mostrar indicador de escritura
            console.log(`${data.name} está escribiendo...`);
        } else {
            // Mostrar mensaje
            console.log(`${data.name}: ${data.message}`);
            if (data.is_admin) {
                console.log('(Administrador)');
            }
        }
    };

    // Manejar errores
    socket.onerror = function(error) {
        console.log('Error WebSocket:', error);
    };

    // Manejar desconexión
    socket.onclose = function(e) {
        console.log('Conexión cerrada');
    };
    ```

    Notas importantes:
    1. La conexión WebSocket requiere autenticación
    2. El usuario debe ser staff para acceder al chat
    3. Los mensajes deben ser enviados en formato JSON
    4. El servidor enviará un indicador de "escribiendo" mientras procesa la respuesta
    """,
    responses={
        200: openapi.Response(
            description="Documentación del WebSocket",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Documentación disponible arriba"
                }
            }
        )
    }
)
@api_view(['GET'])
def chat_docs(request):
    """
    Documentación del WebSocket Chat
    """
    return Response({
        "status": "success",
        "message": "Documentación disponible arriba"
    })
