import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import jwt
from django.conf import settings
from django.db.models import Count, Avg, F
from products.models import Product, Sale

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

    async def process_with_ai(self, message, user):
        """Procesa el mensaje con IA y retorna una respuesta"""
        try:
            # Si el mensaje contiene palabras clave relacionadas con ventas
            if any(keyword in message.lower() for keyword in ['venta', 'ventas', 'vendido', 'vendidos']):
                sales_data = await self.get_sales_data()
                if sales_data:
                    return f"""
                    📊 Resumen de Ventas:
                    
                    Total de ventas: {sales_data['total_sales']}
                    Ingresos totales: ${sales_data['total_revenue']}
                    
                    🏆 Productos más vendidos:
                    {chr(10).join(f"- {p['name']}: {p['quantity']} unidades" for p in sales_data['top_products'])}
                    
                    🕒 Ventas recientes:
                    {chr(10).join(f"- {s['product']['name']}: {s['product']['quantity']} x ${s['product']['unit_price']}" for s in sales_data['recent_sales'])}
                    """
                else:
                    return "Lo siento, no pude obtener los datos de ventas en este momento."

            # Si el mensaje contiene palabras clave relacionadas con productos
            elif any(keyword in message.lower() for keyword in ['producto', 'productos', 'inventario', 'stock']):
                products = await self.get_products_data()
                if products:
                    return f"""
                    📦 Productos disponibles:
                    
                    {chr(10).join(f"- {p['name']}: ${p['base_price']} ({p['current_stock']} en stock)" for p in products[:5])}
                    
                    Total de productos: {len(products)}
                    """
                else:
                    return "Lo siento, no pude obtener los datos de productos en este momento."

            # Respuesta genérica usando el contexto
            user_name = user.name if user.name else "visitante"
            
            if user.is_admin:
                return f"""Hola administrador {user_name}, ¿en qué puedo ayudarte? 
                
                Puedo ayudarte con:
                📊 Consultar ventas y estadísticas
                📦 Ver inventario y productos
                💰 Revisar ingresos
                """
            else:
                return f"""Hola {user_name}, ¿en qué puedo ayudarte? 
                
                Puedo ayudarte con:
                🛍️ Buscar productos
                💡 Información de productos
                📦 Consultar stock
                """
            
        except Exception as e:
            logger.error(f"Error en process_with_ai: {str(e)}")
            return "Lo siento, no puedo procesar tu solicitud en este momento. Por favor, intenta más tarde."

    async def disconnect(self, close_code):
        """
        Maneja la desconexión del WebSocket
        """
        logger.info(f"Cliente desconectado con código: {close_code}")