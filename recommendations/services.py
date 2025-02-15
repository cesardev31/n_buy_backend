from products.models import Product
from .models import UserPreference
from django.db.models import Avg

class RecommendationService:
    @staticmethod
    def get_user_recommendations(user):
        # Obtener todas las preferencias del usuario
        user_preferences = UserPreference.objects.filter(user=user)
        
        # Obtener todos los productos
        all_products = Product.objects.all()
        
        recommendations = {
            'highly_recommended': [],
            'recommended': [],
            'not_recommended': []
        }

        for product in all_products:
            # Calcular score basado en preferencias previas
            avg_rating = UserPreference.objects.filter(
                product=product
            ).aggregate(Avg('rating'))['rating__avg'] or 0

            # Obtener preferencias similares de usuarios
            similar_preferences = UserPreference.objects.filter(
                user__in=UserPreference.objects.filter(
                    product__in=user_preferences.values_list('product', flat=True)
                ).values_list('user', flat=True)
            )

            # Calcular score final
            final_score = (avg_rating * 0.7) + (
                similar_preferences.filter(product=product).aggregate(
                    Avg('rating')
                )['rating__avg'] or 0
            ) * 0.3

            # Clasificar producto
            if final_score >= 2.5:
                recommendations['highly_recommended'].append(product)
            elif final_score >= 1.5:
                recommendations['recommended'].append(product)
            else:
                recommendations['not_recommended'].append(product)

        return recommendations