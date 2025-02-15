from django.db.models import Count, Avg, Q
from products.models import Product, Sale, Inventory
from .models import UserPreference, ProductRecommendation
import numpy as np
from datetime import timedelta
from django.utils import timezone

class RecommendationEngine:
    def __init__(self):
        self.category_weights = {
            'brand': 0.3,
            'category': 0.4,
            'price_range': 0.3
        }

    def calculate_recommendations(self, user):
        """Calcula recomendaciones para un usuario basado en sus preferencias y el historial de compras"""
        try:
            # Obtener preferencias del usuario
            preferences = UserPreference.objects.filter(user=user)
            
            # Obtener productos disponibles
            available_products = Product.objects.filter(
                inventory__quantity__gt=0
            ).distinct()

            # Calcular puntuación para cada producto
            recommendations = []
            for product in available_products:
                score = self._calculate_product_score(product, user, preferences)
                recommendation_type = self._get_recommendation_type(score)
                
                # Actualizar o crear recomendación
                ProductRecommendation.objects.update_or_create(
                    user=user,
                    product=product,
                    defaults={
                        'score': score,
                        'recommendation_type': recommendation_type
                    }
                )

            return True
        except Exception as e:
            print(f"Error calculando recomendaciones: {str(e)}")
            return False

    def _calculate_product_score(self, product, user, preferences):
        """Calcula la puntuación de un producto para un usuario específico"""
        score = 0.0
        
        # 1. Preferencias de categoría
        category_preference = preferences.filter(category=product.category).first()
        if category_preference:
            score += category_preference.weight * self.category_weights['category']
        
        # 2. Preferencias de marca
        brand_preference = preferences.filter(category=product.brand).first()
        if brand_preference:
            score += brand_preference.weight * self.category_weights['brand']
        
        # 3. Rango de precios
        user_avg_price = Sale.objects.filter(user=user).aggregate(Avg('unit_price'))['unit_price__avg']
        if user_avg_price:
            price_diff = abs(float(product.current_price) - float(user_avg_price))
            price_score = 1.0 / (1.0 + price_diff/1000)  # Normalizar diferencia
            score += price_score * self.category_weights['price_range']
        
        # 4. Popularidad del producto
        total_sales = Sale.objects.filter(product=product).count()
        popularity_score = min(total_sales / 100, 1.0)  # Normalizar a máximo 1.0
        score += popularity_score * 0.2
        
        # 5. Descuentos activos
        if product.discount_percentage > 0:
            score += 0.1
        
        return min(score, 1.0)  # Normalizar score final

    def _get_recommendation_type(self, score):
        """Determina el tipo de recomendación basado en el score"""
        if score >= 0.7:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'

    def update_user_preferences(self, user, product):
        """Actualiza las preferencias del usuario basado en una compra o interacción"""
        try:
            # Actualizar preferencia de categoría
            UserPreference.objects.update_or_create(
                user=user,
                category=product.category,
                defaults={'weight': 1.0}
            )
            
            # Actualizar preferencia de marca
            UserPreference.objects.update_or_create(
                user=user,
                category=product.brand,
                defaults={'weight': 1.0}
            )
            
            return True
        except Exception as e:
            print(f"Error actualizando preferencias: {str(e)}")
            return False

    def get_recommendations_by_type(self, user, recommendation_type=None):
        """Obtiene productos recomendados por tipo"""
        query = ProductRecommendation.objects.filter(user=user)
        
        if recommendation_type:
            query = query.filter(recommendation_type=recommendation_type)
        
        return query.select_related('product').order_by('-score')
