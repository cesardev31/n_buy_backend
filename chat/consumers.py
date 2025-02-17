import json
import os
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
import google.generativeai as genai
from asgiref.sync import sync_to_async
from .models import ChatSession, ChatMessage
from products.models import Product, Sale, Inventory
from django.conf import settings
from channels.auth import login
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from recommendations.ai_recommendations import AIRecommendationEngine
from recommendations.models import RecommendationType
from jwt import decode as jwt_decode
import logging
from django.db.models import Count, Avg, Sum, F, Q
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger('django.request')
User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = str(uuid.uuid4())
        self.user = None
        self.user_name = None
        self.is_admin = False
        self.products_cache = None
        self.last_cache_update = None
        self.authenticated = False
        
        logger.info(f"Nueva conexión iniciada: {self.session_id}")
        
        if not hasattr(settings, 'GOOGLE_API_KEY') or not settings.GOOGLE_API_KEY:
            logger.error("Error: GOOGLE_API_KEY no está configurada en settings")
            await self.close()
            return
            
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

        self.room_name = f"session_{self.session_id}"
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Conexión aceptada para sesión: {self.session_id}")

        # Enviar mensaje de conexión como JSON
        await self.send(json.dumps({
            "type": "connection_established",
            "message": "Conexión establecida",
            "session_id": self.session_id,
            "is_bot": True,
            "name": "Sistema"
        }))

        # Solicitar autenticación
        await self.send(json.dumps({
            "type": "auth_required",
            "message": "Por favor, proporciona tu token de autenticación",
            "is_bot": True,
            "name": "Sistema"
        }))

    async def authenticate_token(self, token):
        """Autenticar token y cachear datos del usuario"""
        if not token:
            raise ValueError("Token no proporcionado")
        
        try:
            algorithm = settings.SIMPLE_JWT['ALGORITHM']
            signing_key = settings.SIMPLE_JWT['SIGNING_KEY']
            user_id_claim = settings.SIMPLE_JWT['USER_ID_CLAIM']
            
            token_data = jwt_decode(
                token, 
                signing_key,
                algorithms=[algorithm],
                options={"verify_signature": True}
            )
            
            user_id = token_data.get(user_id_claim)
            if not user_id:
                raise ValueError("Token no contiene user_id")
            
            # Obtener y cachear datos del usuario
            self.user = await database_sync_to_async(User.objects.get)(id=user_id)
            self.user_name = self.user.name if hasattr(self.user, 'name') and self.user.name else self.user.email
            self.is_admin = self.user.is_admin if hasattr(self.user, 'is_admin') else self.user.is_staff
            self.authenticated = True
            
            logger.info(f"Usuario autenticado: {self.user_name} (admin: {self.is_admin})")
            return True
            
        except jwt_decode.ExpiredSignatureError:
            logger.error("Token expirado")
            raise ValueError("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
        except Exception as e:
            logger.error(f"Error de autenticación: {str(e)}")
            raise ValueError(f"Error de autenticación: {str(e)}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            
            # Si no está autenticado, esperar token
            if not self.authenticated:
                token = text_data_json.get("token")
                if not token:
                    await self.send(json.dumps({
                        "type": "error",
                        "message": "Token no proporcionado",
                        "is_bot": True,
                        "name": "Sistema"
                    }))
                    return
                
                try:
                    await self.authenticate_token(token)
                    welcome_message = (
                        f"👋 ¡Hola {self.user_name}! Soy el asistente virtual de Buy n Large.\n\n"
                        "Te puedo ayudar con:\n"
                        "🔍 • Buscar productos específicos\n"
                        "📦 • Consultar disponibilidad y precios\n"
                        "❓ • Responder tus dudas sobre nuestros productos\n\n"
                        "¿En qué puedo ayudarte hoy?"
                    )
                    await self.send(json.dumps({
                        "type": "auth_success",
                        "message": welcome_message,
                        "is_bot": True,
                        "name": "Buy n Large",
                        "is_admin": self.is_admin
                    }))
                    return
                except ValueError as e:
                    await self.send(json.dumps({
                        "type": "error",
                        "message": "Error de autenticación. Por favor, inicia sesión nuevamente.",
                        "is_bot": True,
                        "name": "Sistema"
                    }))
                    if "expirado" in str(e).lower():
                        await self.close()
                    return

            # Procesar mensaje del chat
            message = text_data_json.get("message", "").strip()
            if not message:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "El mensaje no puede estar vacío",
                    "is_bot": True,
                    "name": "Sistema"
                }))
                return

            try:
                # Guardar mensaje del usuario
                await sync_to_async(ChatMessage.objects.create)(
                    anonymous_session_id=self.session_id,
                    user=self.user,
                    content=message,
                    is_user=True
                )

                # Enviar el mensaje del usuario al chat
                await self.send(json.dumps({
                    "type": "chat_message",
                    "message": message,
                    "is_bot": False,
                    "name": self.user_name
                }))

                # Indicador de escritura
                await self.send(json.dumps({
                    "type": "chat_message",
                    "message": "⌛ Procesando tu solicitud...",
                    "is_bot": True,
                    "name": "Buy n Large",
                    "is_typing": True
                }))

                # Procesar con AI y obtener respuesta
                response_text = await self.process_with_ai(message)
                
                if response_text:
                    try:
                        # Guardar respuesta del bot
                        await sync_to_async(ChatMessage.objects.create)(
                            anonymous_session_id=self.session_id,
                            user=self.user,
                            content=response_text,
                            is_user=False
                        )

                        # Enviar la respuesta del bot
                        await self.send(json.dumps({
                            "type": "chat_message",
                            "message": response_text,
                            "is_bot": True,
                            "name": "Buy n Large"
                        }, cls=DecimalEncoder))
                    except Exception as e:
                        logger.error(f"Error al guardar respuesta del bot: {str(e)}")
                        # Aún enviamos la respuesta aunque falle el guardado
                        await self.send(json.dumps({
                            "type": "chat_message",
                            "message": response_text,
                            "is_bot": True,
                            "name": "Buy n Large"
                        }, cls=DecimalEncoder))
                else:
                    await self.send(json.dumps({
                        "type": "error",
                        "message": "Lo siento, no pude procesar tu solicitud en este momento. Por favor, intenta más tarde.",
                        "is_bot": True,
                        "name": "Sistema"
                    }))

            except Exception as db_error:
                logger.error(f"Error de base de datos: {str(db_error)}")
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Lo siento, hubo un problema al procesar tu mensaje. Por favor, intenta más tarde.",
                    "is_bot": True,
                    "name": "Sistema"
                }))

        except Exception as e:
            logger.error(f"Error en receive: {str(e)}")
            await self.send(json.dumps({
                "type": "error",
                "message": "Lo siento, ocurrió un error inesperado. Por favor, intenta más tarde.",
                "is_bot": True,
                "name": "Sistema"
            }))

    @sync_to_async
    def get_products_data(self, force_refresh=False):
        """Obtener datos de productos con caché"""
        current_time = datetime.now()
        cache_duration = timedelta(minutes=5)

        if (not self.products_cache or 
            not self.last_cache_update or 
            force_refresh or 
            current_time - self.last_cache_update > cache_duration):
            
            # Obtener productos con sus métricas
            self.products_cache = list(Product.objects.annotate(
                total_sales=Count('sale'),
                avg_rating=Avg('ratings__score'),
                total_ratings=Count('ratings'),
                current_stock=F('inventory__quantity'),
            ).values(
                'id', 'name', 'category', 'brand', 'base_price',
                'description', 'total_sales', 'avg_rating', 
                'total_ratings', 'current_stock'
            ))
            
            self.last_cache_update = current_time
            
        return self.products_cache

    async def get_sales_data(self):
        try:
            # Obtener todas las ventas con select_related para optimizar
            sales = await sync_to_async(lambda: list(Sale.objects.select_related('product', 'user').order_by('-created_at')))()
            
            sales_data = []
            for sale in sales:
                try:
                    sale_dict = {
                        'id': sale.id,
                        'total': float(sale.total_price),
                        'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'product': {
                            'name': sale.product.name,  # Ya no necesitamos sync_to_async aquí
                            'quantity': sale.quantity,
                            'unit_price': float(sale.unit_price)
                        }
                    }
                    sales_data.append(sale_dict)
                except Exception as e:
                    logger.error(f"Error procesando venta {sale.id}: {str(e)}")
                    continue
            
            # Calcular estadísticas
            if sales_data:
                total_sales = len(sales_data)
                total_revenue = sum(sale['total'] for sale in sales_data)
                
                # Contar productos vendidos
                product_counts = {}
                for sale in sales_data:
                    name = sale['product']['name']
                    quantity = sale['product']['quantity']
                    product_counts[name] = product_counts.get(name, 0) + quantity
                
                top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                
                return {
                    'total_sales': total_sales,
                    'total_revenue': total_revenue,
                    'recent_sales': sales_data[:5],  # Cambiado a [:5] ya que ya está ordenado por fecha
                    'top_products': [{'name': name, 'quantity': qty} for name, qty in top_products]
                }
            
            return {
                'total_sales': 0,
                'total_revenue': 0,
                'recent_sales': [],
                'top_products': []
            }
            
        except Exception as e:
            logger.error(f"Error al obtener datos de ventas: {str(e)}")
            return None

    async def process_with_ai(self, message):
        try:
            # Si el mensaje contiene palabras clave relacionadas con ventas
            if any(keyword in message.lower() for keyword in ['venta', 'ventas', 'vendido', 'vendidos']):
                try:
                    # Agregar timeout para la obtención de datos
                    import asyncio
                    sales_data = await asyncio.wait_for(self.get_sales_data(), timeout=5.0)
                    
                    if sales_data:
                        sales_context = (
                            f"Datos de ventas:\n"
                            f"Total de ventas realizadas: {sales_data['total_sales']}\n"
                            f"Ingresos totales: ${sales_data['total_revenue']:.2f}\n"
                            f"Productos más vendidos:\n"
                        )
                        
                        for product in sales_data['top_products']:
                            sales_context += f"- {product['name']}: {product['quantity']} unidades\n"
                        
                        sales_context += "\nVentas recientes:\n"
                        for sale in sales_data['recent_sales']:
                            sales_context += (
                                f"- Venta #{sale['id']} - ${sale['total']:.2f} - {sale['date']}\n"
                                f"  • {sale['product']['name']} x{sale['product']['quantity']} "
                                f"(${sale['product']['unit_price']:.2f} c/u)\n"
                            )
                    else:
                        sales_context = "No se pudieron obtener los datos de ventas en este momento."
                    
                    prompt = f"""Actúa como un asistente de ventas profesional. 
                    
                    Datos actuales:
                    {sales_context}
                    
                    Pregunta del usuario: {message}
                    
                    Responde de manera profesional, incluyendo los datos relevantes y formatéando los números de manera adecuada."""
                    
                except asyncio.TimeoutError:
                    logger.error("Timeout al obtener datos de ventas")
                    prompt = f"Actúa como un asistente de ventas profesional. Lo siento, la consulta está tomando más tiempo del esperado. ¿Podrías intentarlo de nuevo en un momento?\n\nPregunta del usuario: {message}"
                except Exception as e:
                    logger.error(f"Error al obtener datos de ventas: {str(e)}")
                    prompt = f"Actúa como un asistente de ventas profesional. Lo siento, no puedo acceder a los datos de ventas en este momento.\n\nPregunta del usuario: {message}"
            else:
                # Obtener datos de productos solo si es necesario
                products = None
                if any(keyword in message.lower() for keyword in ['producto', 'precio', 'stock', 'disponible']):
                    try:
                        products = await self.get_products_data()
                    except Exception as e:
                        logger.error(f"Error al obtener datos de productos: {str(e)}")
                        products = None

                # Crear el prompt para el asistente
                system_context = f"""
                Eres el asistente virtual de Buy n Large, una tienda de tecnología.
                
                Información del usuario:
                👤 Nombre: {self.user_name}
                🔑 Rol: {'Administrador' if self.is_admin else 'Cliente'}
                
                {"" if not products else f'''
                Información de productos disponibles:
                {json.dumps(products, indent=2, cls=DecimalEncoder)}
                '''}
                
                Tus responsabilidades:
                1. Ayudar a los usuarios a encontrar productos
                2. Responder preguntas sobre productos y servicios
                3. Proporcionar soporte técnico básico
                4. Ser amable y profesional en todo momento
                
                Reglas:
                1. Si te preguntan por un producto específico, proporciona detalles relevantes
                2. Si no tienes información sobre algo, indícalo honestamente
                3. Mantén las respuestas concisas pero informativas
                4. Usa emojis ocasionalmente para hacer la conversación más amigable
                5. Si muestras precios, formatea los números correctamente
                6. Para administradores, incluye información de ventas cuando sea relevante
                
                Si no puedes acceder a algún dato, indícalo amablemente sin revelar detalles técnicos.
                """

                prompt = f"{system_context}\n\nUsuario: {message}\n\nAsistente:"

            try:
                response = await sync_to_async(self.model.generate_content)(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Error al generar respuesta AI: {str(e)}")
                return "Lo siento, estoy teniendo problemas para procesar tu solicitud. ¿Podrías intentarlo de nuevo?"

        except Exception as e:
            logger.error(f"Error en process_with_ai: {str(e)}")
            return "Lo siento, no puedo procesar tu solicitud en este momento. Por favor, intenta más tarde."

    async def disconnect(self, close_code):
        # Dejar el grupo de chat
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def chat_message(self, event):
        try:
            message = event["message"]
            is_bot = event["is_bot"]
            is_typing = event.get("is_typing", False)
            name = event.get("name", "Usuario")
            is_admin = event.get("is_admin", False)

            await self.send(json.dumps({
                "type": "chat_message",
                "message": message,
                "is_bot": is_bot,
                "is_typing": is_typing,
                "name": name,
                "is_admin": is_admin
            }))
        except Exception as e:
            logger.error(f"Error en chat_message: {str(e)}")