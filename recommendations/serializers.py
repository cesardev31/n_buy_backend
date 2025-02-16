from rest_framework import serializers
from .models import UserPreference, ProductRecommendation
from products.serializers import ProductSerializer

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['id', 'user', 'product', 'rating', 'category', 'weight', 'created_at', 'last_updated']

class ProductRecommendationSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = ProductRecommendation
        fields = ['id', 'user', 'product', 'score', 'recommendation_type', 'last_updated']
