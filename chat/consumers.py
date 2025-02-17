import json
import logging
import google.generativeai as genai
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import jwt
from django.conf import settings
from django.db.models import Count, Avg, F
from products.models import Product, Sale
from decimal import Decimal

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products_cache = None

    async def connect(self):
        """
        Maneja la conexión inicial del WebSocket.
        """
        logger.info("Nueva conexión WebSocket iniciada")
        await self.accept()
        logger.info("Conexión WebSocket aceptada")
        
        # Enviar mensaje de bienvenida
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': 'Bienvenido al chat de Buy n Large'
        }))

    async def receive(self, text_data):
        """
        Maneja los mensajes recibidos en formato texto.
        """
        try:
            logger.info(f"Mensaje recibido: {text_data[:100]}...")  # Log primeros 100 caracteres
            data = json.loads(text_data)
            logger.info(f"Mensaje JSON decodificado: {data}")
            
            # Verificar que el mensaje tenga el token
            if 'token' not in data:
                logger.error("Token no proporcionado en el mensaje")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Token no proporcionado'
                }))
                return

            # Extraer datos del token sin validarlo
            try:
                # Decodificar el token sin verificar la firma
                token_data = jwt.decode(data['token'], options={"verify_signature": False})
                user_id = token_data.get('user_id')
                
                if not user_id:
                    logger.error("user_id no encontrado en el token")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Token no contiene user_id'
                    }))
                    return
                
                User = get_user_model()
                user = await sync_to_async(User.objects.get)(id=user_id)
                logger.info(f"Usuario identificado: {user.username}")
                
            except Exception as e:
                logger.error(f"Error extrayendo datos del token: {str(e)}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Error procesando token'
                }))
                return

            # Procesar el mensaje según su tipo
            if data.get('type') == 'chat_message':
                message = data.get('message', '').strip()
                if message:
                    logger.info(f"Procesando mensaje de chat: {message[:50]}...")
                    response = await self.process_with_ai(message, user)
                    await self.send(text_data=json.dumps({
                        'type': 'chat_message',
                        'message': response,
                        'is_bot': True,
                        'name': 'Buy n Large'
                    }))
                    logger.info("Respuesta enviada exitosamente")
                else:
                    logger.warning("Mensaje de chat vacío recibido")
            else:
                logger.warning(f"Tipo de mensaje desconocido: {data.get('type')}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensaje inválido'
            }))
        except Exception as e:
            logger.error(f"Error inesperado procesando mensaje: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error interno del servidor'
            }))

    @sync_to_async
    def get_products_data(self):
        """Obtener datos de productos"""
        try:
            if not self.products_cache:
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
            return self.products_cache
        except Exception as e:
            logger.error(f"Error obteniendo productos: {str(e)}")
            return None

    @sync_to_async
    def get_sales_data(self):
        """Obtener datos de ventas"""
        try:
            # Obtener ventas recientes
            sales = Sale.objects.select_related('product').order_by('-id')[:5]
            
            sales_data = []
            total_revenue = 0
            product_counts = {}
            
            for sale in sales:
                sale_dict = {
                    'product': {
                        'name': sale.product.name,
                        'quantity': sale.quantity,
                        'unit_price': float(sale.unit_price)
                    }
                }
                sales_data.append(sale_dict)
                
                total_revenue += float(sale.total_price)
                product_counts[sale.product.name] = product_counts.get(sale.product.name, 0) + sale.quantity
            
            # Obtener productos más vendidos
            top_products = [
                {'name': name, 'quantity': qty} 
                for name, qty in sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
            ][:3]
            
            return {
                'total_sales': len(sales_data),
                'total_revenue': total_revenue,
                'recent_sales': sales_data,
                'top_products': top_products
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo ventas: {str(e)}")
            return None

    def decimal_to_float(self, obj):
        """Convierte objetos Decimal a float para serialización JSON"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self.decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self.decimal_to_float(x) for x in obj]
        return obj

    async def process_with_ai(self, message, user):
        """Procesa el mensaje con IA usando Google AI (Gemini)"""
        try:
            # Obtener datos contextuales
            products = await self.get_products_data()
            sales_data = await self.get_sales_data()
            
            # Convertir Decimal a float para serialización
            products = self.decimal_to_float(products) if products else None
            sales_data = self.decimal_to_float(sales_data) if sales_data else None
            
            # Configurar Google AI
            if not hasattr(settings, 'GOOGLE_API_KEY') or not settings.GOOGLE_API_KEY:
                logger.error("GOOGLE_API_KEY no está configurada en settings")
                return "Lo siento, hay un problema con la configuración del sistema."
                
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            # Crear el prompt con el contexto
            prompt = f"""
            Eres el asistente virtual oficial de Buy n Large. Tu nombre es "Buy n Large Assistant".
            
            INSTRUCCIONES IMPORTANTES:
            1. SIEMPRE identifícate como "Buy n Large Assistant" al inicio de cada respuesta.
            2. NUNCA uses otro nombre o te identifiques de otra manera.
            3. Sé conciso y directo en tus respuestas.
            4. Si el usuario pregunta por productos o ventas, incluye datos específicos.
            5. Mantén un tono profesional y amigable.
            
            Contexto del usuario:
            - Nombre: {user.username}
            - Rol: {'Administrador' if user.is_staff else 'Cliente'}
            
            Datos de productos disponibles:
            {json.dumps(products, indent=2) if products else 'No hay datos de productos disponibles'}
            
            Datos de ventas recientes:
            {json.dumps(sales_data, indent=2) if sales_data else 'No hay datos de ventas disponibles'}
            
            Mensaje del usuario: {message}
            """
            
            # Generar respuesta usando el modelo
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error procesando mensaje con IA: {str(e)}")
            return "Lo siento, hubo un problema al procesar tu mensaje. Por favor, inténtalo de nuevo."

    async def disconnect(self, close_code):
        """
        Maneja la desconexión del WebSocket
        """
        logger.info(f"Cliente desconectado con código: {close_code}")