import google.generativeai as genai
from django.conf import settings
from products.models import Product
from django.db.models import Avg, Count
from asgiref.sync import sync_to_async
import json

class AIRecommendationEngine:
    def __init__(self):
        if not hasattr(settings, 'GOOGLE_API_KEY') or not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY no está configurada en settings")
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    @sync_to_async
    def get_product_data(self):
        """Obtener datos de productos para enviar al modelo"""
        products = Product.objects.annotate(
            avg_rating=Avg('ratings__score'),
            num_ratings=Count('ratings'),
            num_sales=Count('order_items')
        ).values(
            'id', 'name', 'category', 'brand', 'base_price',
            'avg_rating', 'num_ratings', 'num_sales'
        )
        return list(products)

    async def get_recommendations(self, user_data, is_admin=False):
        """Obtener recomendaciones usando Google AI"""
        products = await self.get_product_data()
        
        # Preparar el prompt según el tipo de usuario
        if is_admin:
            prompt = self._create_admin_prompt(products)
        else:
            prompt = self._create_user_prompt(products, user_data)

        try:
            # Generar respuesta usando el modelo
            response = await self.model.generate_content(prompt)
            response_text = response.text
            
            # Asegurarnos de que la respuesta es JSON válido
            # Si la respuesta contiene texto antes o después del JSON, lo limpiamos
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                recommendations = json.loads(json_str)
            else:
                raise ValueError("No se encontró JSON válido en la respuesta")

            # Validar y estructurar la respuesta
            return {
                'highly_recommended': recommendations.get('highly_recommended', []),
                'recommended': recommendations.get('recommended', []),
                'not_recommended': recommendations.get('not_recommended', [])
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear la respuesta del modelo: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error al generar recomendaciones: {str(e)}")

    def _create_admin_prompt(self, products):
        """Crear prompt para administradores"""
        return f"""
        Actúa como un sistema de recomendación de productos. 
        Analiza los siguientes productos y sus métricas:
        {json.dumps(products, indent=2)}

        Como administrador, necesito que clasifiques los productos en tres categorías 
        basándote en ventas, ratings y número de reseñas:
        1. Altamente Recomendado (productos más vendidos y mejor calificados)
        2. Recomendado (productos con rendimiento promedio)
        3. No Recomendado (productos con bajo rendimiento)

        IMPORTANTE: Debes responder SOLO con un objeto JSON con esta estructura exacta:
        {
            "highly_recommended": [{"id": product_id, "reason": "razón de la clasificación"}],
            "recommended": [{"id": product_id, "reason": "razón de la clasificación"}],
            "not_recommended": [{"id": product_id, "reason": "razón de la clasificación"}]
        }
        """

    def _create_user_prompt(self, products, user_data):
        """Crear prompt personalizado para usuarios"""
        return f"""
        Actúa como un sistema de recomendación de productos personalizado.
        Datos del usuario:
        {json.dumps(user_data, indent=2)}

        Productos disponibles:
        {json.dumps(products, indent=2)}

        Basándote en el historial de compras del usuario, sus preferencias y comportamiento,
        clasifica los productos en tres categorías:
        1. Altamente Recomendado (productos que mejor se ajustan a sus preferencias)
        2. Recomendado (productos que podrían interesarle)
        3. No Recomendado (productos que probablemente no le interesen)

        IMPORTANTE: Debes responder SOLO con un objeto JSON con esta estructura exacta:
        {
            "highly_recommended": [{"id": product_id, "reason": "razón personalizada de la recomendación"}],
            "recommended": [{"id": product_id, "reason": "razón personalizada de la recomendación"}],
            "not_recommended": [{"id": product_id, "reason": "razón personalizada de la recomendación"}]
        }
        """
