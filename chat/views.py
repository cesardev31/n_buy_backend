from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

@login_required
def chat_test(request):
    """
    Vista para cargar la interfaz de chat.
    Genera automáticamente un token JWT para el usuario autenticado.
    """
    # Generar token JWT para el usuario
    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    
    # Debug: mostrar el token
    print("\nTOKEN PARA WEBSOCKET:")
    print("="*50)
    print(access_token)
    print("="*50)
    print()
    
    context = {
        'token': access_token,
        'ws_url': f"{'wss' if request.is_secure() else 'ws'}://{request.get_host()}/ws/chat/",
        'user_name': request.user.email or request.user.username,
    }
    
    return render(request, 'chat/test.html', context)