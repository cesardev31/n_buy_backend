from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Obtener el token del header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            # Verificar formato "Bearer <token>"
            if not auth_header.startswith('Bearer '):
                raise exceptions.AuthenticationFailed('El formato del token debe ser: Bearer <token>')
            
            token = auth_header.split(' ')[1]
            
            # Obtener la configuración de JWT
            algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')
            signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)
            user_id_claim = settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id')
            token_type_claim = settings.SIMPLE_JWT.get('TOKEN_TYPE_CLAIM', 'token_type')
            
            # Decodificar sin verificar para obtener el tipo de token
            unverified_payload = jwt_decode(token, options={"verify_signature": False})
            
            # Verificar que sea un token de acceso
            if unverified_payload.get(token_type_claim) != 'access':
                raise exceptions.AuthenticationFailed('Solo se permiten tokens de acceso en el header')
            
            # Decodificar y verificar el token
            payload = jwt_decode(token, signing_key, algorithms=[algorithm])
            
            # Obtener el usuario
            user = User.objects.get(id=payload.get(user_id_claim))
            
            return (user, token)
            
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuario no encontrado')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Token inválido: {str(e)}')

def validate_token(view_func):
    """
    Decorador para validar el token JWT en el header Authorization
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return Response(
                {'error': 'Se requiere token de autorización'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'El formato del token debe ser: Bearer <token>'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        try:
            token = auth_header.split(' ')[1]
            
            # Obtener la configuración de JWT
            algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')
            signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)
            user_id_claim = settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id')
            token_type_claim = settings.SIMPLE_JWT.get('TOKEN_TYPE_CLAIM', 'token_type')
            
            # Decodificar sin verificar para obtener el tipo de token
            unverified_payload = jwt_decode(token, options={"verify_signature": False})
            
            # Verificar que sea un token de acceso
            if unverified_payload.get(token_type_claim) != 'access':
                return Response(
                    {'error': 'Solo se permiten tokens de acceso en el header'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Decodificar y verificar el token
            payload = jwt_decode(token, signing_key, algorithms=[algorithm])
            
            # Obtener el usuario
            user = User.objects.get(id=payload.get(user_id_claim))
            
            # Agregar el usuario y el token al request
            request.user = user
            request.auth = token
            
            return view_func(request, *args, **kwargs)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Token inválido: {str(e)}'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    return wrapped_view

def extract_token_data(token):
    """
    Valida un token JWT y extrae los datos del usuario
    Returns: (user_id, is_admin)
    """
    try:
        # Obtener la configuración de JWT
        algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')
        signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)
        user_id_claim = settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id')
        token_type_claim = settings.SIMPLE_JWT.get('TOKEN_TYPE_CLAIM', 'token_type')
        
        # Decodificar y verificar el token
        payload = jwt_decode(token, signing_key, algorithms=[algorithm])
        
        # Verificar que sea un token de acceso
        if payload.get(token_type_claim) != 'access':
            raise ValueError('Token inválido: no es un token de acceso')
            
        user_id = payload.get(user_id_claim)
        is_admin = payload.get('is_admin', False)
        
        if not user_id:
            raise ValueError('Token inválido: no contiene user_id')
            
        return user_id, is_admin
        
    except Exception as e:
        raise ValueError(f'Token inválido: {str(e)}')
