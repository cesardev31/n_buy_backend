import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from n_buy_backend.asgi import application
from chat.consumers import ChatConsumer
from chat.models import ChatSession, ChatMessage

@pytest.mark.asyncio
async def test_chat_consumer():
    # Crear usuario de prueba
    User = get_user_model()
    user = await sync_to_async(User.objects.create_user)(
        email='admin@example.com',
        name='Test User',
        password='admin123'
    )

    # Crear comunicador WebSocket
    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/"
    )
    communicator.scope["user"] = user

    # Conectar
    connected, _ = await communicator.connect()
    assert connected

    # Enviar mensaje
    await communicator.send_json_to({
        "message": "¿Qué productos me recomiendas?"
    })

    # Recibir respuesta
    response = await communicator.receive_json_from()
    assert "message" in response
    assert "is_bot" in response
    assert response["is_bot"] is True

    # Desconectar
    await communicator.disconnect() 