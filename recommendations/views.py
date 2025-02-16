from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg
from products.models import Product
from jwt import decode as jwt_decode
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import google.generativeai as genai
import json
from .serializers import ProductRecommendationSerializer

# Definir esquemas de Swagger
product_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del producto'),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre del producto'),
        'brand': openapi.Schema(type=openapi.TYPE_STRING, description='Marca del producto'),
        'category': openapi.Schema(type=openapi.TYPE_STRING, description='Categoría del producto'),
        'base_price': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='Precio base del producto'),
        'avg_rating': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='Calificación promedio'),
        'num_ratings': openapi.Schema(type=openapi.TYPE_INTEGER, description='Número de calificaciones'),
        'num_sales': openapi.Schema(type=openapi.TYPE_INTEGER, description='Número de ventas'),
        'image_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL de la imagen del producto')
    }
)

recommendation_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'product': product_schema,
        'reason': openapi.Schema(type=openapi.TYPE_STRING, description='Razón de la recomendación')
    }
)

recommendations_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'highly_recommended': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=recommendation_item_schema,
            description='Lista de productos altamente recomendados'
        ),
        'recommended': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=recommendation_item_schema,
            description='Lista de productos recomendados'
        ),
        'not_recommended': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=recommendation_item_schema,
            description='Lista de productos no recomendados'
        )
    }
)

error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Mensaje de error principal'),
        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Detalles adicionales del error')
    }
)

def get_ai_recommendations(products_data, user_data, is_admin):
    """Obtiene recomendaciones usando Google AI"""
    try:
        if not hasattr(settings, 'GOOGLE_API_KEY') or not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY no está configurada en settings")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Crear el prompt según el tipo de usuario
        if is_admin:
            prompt = f"""
            Actúa como un sistema de recomendación de productos. 
            Analiza los siguientes productos y sus métricas:
            {json.dumps(products_data, indent=2)}

            Como administrador, necesito que clasifiques los productos en tres categorías 
            basándote en ventas, ratings y número de reseñas:
            1. Altamente Recomendado (productos más vendidos y mejor calificados)
            2. Recomendado (productos con rendimiento promedio)
            3. No Recomendado (productos con bajo rendimiento)
            """
        else:
            # Verificar si el usuario tiene historial o preferencias
            has_history = any([
                user_data['preferences']['categories'],
                user_data['preferences']['recent_views'],
                user_data['preferences']['cart_items']
            ])

            if has_history:
                prompt = f"""
                Actúa como un sistema de recomendación de productos personalizado.
                Datos del usuario:
                {json.dumps(user_data, indent=2)}

                Productos disponibles:
                {json.dumps(products_data, indent=2)}

                Basándote en el historial de compras del usuario, sus preferencias y comportamiento,
                clasifica los productos en tres categorías:
                1. Altamente Recomendado (productos que mejor se ajustan a sus preferencias)
                2. Recomendado (productos que podrían interesarle)
                3. No Recomendado (productos que probablemente no le interesen)
                """
            else:
                prompt = f"""
                Actúa como un sistema de recomendación de productos.
                No hay historial de usuario disponible, así que basaremos las recomendaciones en las características de los productos.

                Productos disponibles:
                {json.dumps(products_data, indent=2)}

                Clasifica los productos en tres categorías basándote en:
                - Relación calidad-precio
                - Popularidad de la categoría
                - Versatilidad y utilidad general
                - Precio (priorizando productos de rango medio)

                1. Altamente Recomendado: Productos versátiles y útiles para la mayoría de los usuarios
                2. Recomendado: Productos específicos pero con buena relación calidad-precio
                3. No Recomendado: Productos muy especializados o de nicho

                IMPORTANTE: Asegúrate de incluir al menos 5 productos en cada categoría.
                """

        prompt += """
        IMPORTANTE: Debes responder SOLO con un objeto JSON con esta estructura exacta:
        {
            "highly_recommended": [{"id": product_id, "reason": "razón de la recomendación"}],
            "recommended": [{"id": product_id, "reason": "razón de la recomendación"}],
            "not_recommended": [{"id": product_id, "reason": "razón de la recomendación"}]
        }
        """

        # Obtener respuesta del modelo
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        # Extraer el JSON de la respuesta
        response_text = response.text
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            # Si falla el parsing, intentar extraer el JSON de la respuesta
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                json_str = json_str.replace('\n', '').replace('\r', '').strip()
                result = json.loads(json_str)
                return result
            raise ValueError("No se encontró JSON válido en la respuesta")

    except Exception as e:
        raise

@swagger_auto_schema(
    method='get',
    operation_id='get_recommendations',
    operation_description="""
    Obtiene recomendaciones de productos personalizadas basadas en el perfil del usuario o métricas generales.
    
    Las recomendaciones se dividen en tres categorías:
    - Altamente Recomendado: Productos que mejor se ajustan al perfil del usuario
    - Recomendado: Productos que podrían interesar al usuario
    - No Recomendado: Productos que probablemente no sean de interés
    
    Para usuarios administradores, las recomendaciones se basan en métricas de ventas y calificaciones.
    Para usuarios regulares, se consideran sus preferencias y comportamiento de compra.
    """,
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Token JWT de autenticación. Debe incluir el prefijo 'Bearer'",
            type=openapi.TYPE_STRING,
            required=True,
            example='Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
        ),
    ],
    responses={
        200: openapi.Response(
            description="Recomendaciones obtenidas exitosamente",
            schema=recommendations_response_schema,
            examples={
                'application/json': {
                    'highly_recommended': [{
                        'product': {
                            'id': 1,
                            'name': 'Producto Ejemplo',
                            'brand': 'Marca',
                            'category': 'Categoría',
                            'base_price': 99.99,
                            'avg_rating': 4.5,
                            'num_ratings': 10,
                            'num_sales': 50,
                            'image_url': 'https://ejemplo.com/imagen.jpg'
                        },
                        'reason': 'Este producto coincide con tus preferencias de compra'
                    }],
                    'recommended': [],
                    'not_recommended': []
                }
            }
        ),
        401: openapi.Response(
            description="No autorizado - Token inválido o expirado",
            schema=error_schema,
            examples={
                'application/json': {
                    'error': 'Token inválido',
                    'detail': 'El token ha expirado'
                }
            }
        ),
        500: openapi.Response(
            description="Error interno del servidor",
            schema=error_schema,
            examples={
                'application/json': {
                    'error': 'Error del servidor',
                    'detail': 'Error al procesar las recomendaciones'
                }
            }
        )
    },
    tags=['recommendations']
)
@api_view(['GET'])
def get_recommendations(request):
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            return Response({
                'error': 'Token no proporcionado',
                'detail': 'No se encontró el header Authorization'
            }, status=401)
            
        if not auth_header.startswith('Bearer '):
            return Response({
                'error': 'Formato de token inválido',
                'detail': 'El header debe ser: Bearer <token>'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verificar la clave secreta
            secret_key = settings.SECRET_KEY
            
            # Intentar decodificar sin verificar primero
            unverified_payload = jwt_decode(token, options={"verify_signature": False})
            
            # Ahora intentar con verificación completa
            payload = jwt_decode(
                token, 
                secret_key, 
                algorithms=['HS256'],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                }
            )
            
            # Validar tipo de token
            token_type = payload.get('token_type')
            if token_type != 'access':
                return Response({
                    'error': 'Token inválido',
                    'detail': f'El token debe ser de tipo access, no {token_type}'
                }, status=401)
            
            # Obtener datos del usuario
            user_id = payload.get('user_id')
            is_admin = payload.get('is_admin', False)
            
            if not user_id:
                return Response({
                    'error': 'Token inválido',
                    'detail': 'El token no contiene información del usuario'
                }, status=401)
                
            user_data = {
                'user_id': user_id,
                'is_admin': is_admin,
                'preferences': {
                    'categories': [],
                    'recent_views': [],
                    'cart_items': []
                }
            }

            # Obtener datos de productos
            products = Product.objects.annotate(
                avg_rating=Avg('ratings__score'),
                num_ratings=Count('ratings'),
                num_sales=Count('sale')
            ).values(
                'id', 'name', 'category', 'brand', 'base_price',
                'avg_rating', 'num_ratings', 'num_sales', 'image_url'
            )
            
            # Convertir valores decimales a strings para serialización JSON
            products_data = []
            for product in products:
                product_dict = dict(product)
                # Convertir Decimal a string
                if product_dict['base_price'] is not None:
                    product_dict['base_price'] = str(product_dict['base_price'])
                if product_dict['avg_rating'] is not None:
                    product_dict['avg_rating'] = str(product_dict['avg_rating'])
                # Asegurar que image_url no sea None
                if product_dict['image_url'] is None:
                    product_dict['image_url'] = ''
                products_data.append(product_dict)

            # Obtener recomendaciones de IA
            try:
                recommendations = get_ai_recommendations(products_data, user_data, is_admin)
                
                if not isinstance(recommendations, dict):
                    raise ValueError("Las recomendaciones deben ser un diccionario")
                
                # Preparar respuesta con datos completos de productos
                products_dict = {
                    p['id']: {
                        'id': p['id'],
                        'name': p['name'],
                        'brand': p['brand'],
                        'category': p['category'],
                        'base_price': p['base_price'],
                        'avg_rating': p['avg_rating'],
                        'num_ratings': p['num_ratings'],
                        'num_sales': p['num_sales'],
                        'image_url': p['image_url']
                    } for p in products_data
                }

                response_data = {
                    'highly_recommended': [],
                    'recommended': [],
                    'not_recommended': []
                }

                for category in response_data.keys():
                    if category in recommendations:
                        for rec in recommendations[category]:
                            if isinstance(rec, dict) and 'id' in rec:
                                product_id = rec['id']
                                product = products_dict.get(product_id)
                                if product:
                                    response_data[category].append({
                                        'product': product,
                                        'reason': rec.get('reason', '')
                                    })

                return Response(response_data)

            except Exception as e:
                return Response(
                    {'error': 'Error al obtener recomendaciones'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': 'Error del servidor', 'details': str(e)},
                status=500
            )
    except Exception as e:
        return Response(
            {'error': 'Error del servidor', 'details': str(e)},
            status=500
        )
