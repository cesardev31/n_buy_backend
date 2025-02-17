from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name', 'email', 'password', 'confirmPassword'],
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre del usuario'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Correo electrónico'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Contraseña'),
            'confirmPassword': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Confirmar contraseña'),
        }
    ),
    responses={
        201: openapi.Response(
            description="Usuario creado exitosamente",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                    'tokens': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            'access': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            )
        ),
        400: 'Datos inválidos',
        500: 'Error del servidor'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    try:
        name = request.data.get('name')
        password = request.data.get('password')
        confirm_password = request.data.get('confirmPassword')
        email = request.data.get('email')

        # Validaciones
        if not name or not password or not email or not confirm_password:
            return Response(
                {'error': 'Todos los campos son obligatorios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if password != confirm_password:
            return Response(
                {'error': 'Las contraseñas no coinciden'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'El email ya está registrado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            name=name,
            email=email,
            password=password
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'password'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Correo electrónico'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Contraseña'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Login exitoso",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                    'tokens': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            'access': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            )
        ),
        400: 'Datos inválidos',
        401: 'Credenciales inválidas',
        404: 'Usuario no encontrado',
        500: 'Error del servidor'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Por favor proporcione email y contraseña'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar el usuario por email
        try:
            user = User.objects.get(email=email)
            
            # Intentar autenticar usando authenticate primero
            auth_user = authenticate(request, email=email, password=password)
            
            if auth_user is not None:
                # La autenticación fue exitosa
                refresh = RefreshToken.for_user(auth_user)
                return Response({
                    'user_id': auth_user.id,
                    'email': auth_user.email,
                    'username': auth_user.username,
                    'is_admin': auth_user.is_admin,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            
            # Si authenticate falló, intentar verificar la contraseña directamente
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user_id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'is_admin': user.is_admin,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            else:
                return Response(
                    {
                        'error': 'Contraseña incorrecta',
                        'debug': {
                            'email_exists': True,
                            'password_check_failed': True
                        }
                    }, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'No existe usuario con este email'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['token'],
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description='Token JWT (puede ser access o refresh token)'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Datos del usuario obtenidos exitosamente",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                    'role': openapi.Schema(type=openapi.TYPE_STRING),
                    'token_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'token_type': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Token inválido',
        401: 'Token expirado o inválido',
        500: 'Error del servidor'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    try:
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Obtener la configuración de JWT
            algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')
            signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)
            
            # Decodificar el token con verificación
            token_data = jwt_decode(
                token, 
                signing_key,
                algorithms=[algorithm],
                options={"verify_signature": True}
            )
            user_id = token_data.get('user_id')
            token_type = token_data.get('token_type', 'unknown')
            
            if not user_id:
                return Response(
                    {'error': 'Token no contiene user_id'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener el usuario
            user = User.objects.get(id=user_id)
            
            return Response({
                'user_id': user.id,
                'email': user.email,
                'role': 'admin' if user.is_admin else 'user',
                'token_data': token_data,
                'token_type': token_type
            })
            
        except TokenError as e:
            return Response(
                {'error': f'Token inválido: {str(e)}'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': f'Error al procesar el token: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
