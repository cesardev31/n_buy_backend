from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Product, Inventory, Rating, Sale
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from recommendations.services import RecommendationService
from django.utils import timezone
import logging

logger = logging.getLogger('django.request')

# Create your views here.

# Productos
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name', 'brand', 'description', 'base_price', 'category'],
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'brand': openapi.Schema(type=openapi.TYPE_STRING),
            'description': openapi.Schema(type=openapi.TYPE_STRING),
            'base_price': openapi.Schema(type=openapi.TYPE_NUMBER),
            'category': openapi.Schema(type=openapi.TYPE_STRING),
            'discount_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
            'discount_start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'discount_end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        }
    )
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_product(request):
    try:
        product = Product.objects.create(
            name=request.data['name'],
            brand=request.data['brand'],
            description=request.data['description'],
            base_price=request.data['base_price'],
            category=request.data['category'],
            discount_percentage=request.data.get('discount_percentage', 0),
            discount_start_date=request.data.get('discount_start_date'),
            discount_end_date=request.data.get('discount_end_date')
        )
        return Response({
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'description': product.description,
            'base_price': str(product.base_price),
            'current_price': str(product.current_price),
            'category': product.category,
            'discount_percentage': str(product.discount_percentage),
            'discount_start_date': product.discount_start_date,
            'discount_end_date': product.discount_end_date,
            'created_at': product.created_at
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_products(request):
    products = Product.objects.all()
    return Response([{
        'id': product.id,
        'name': product.name,
        'brand': product.brand,
        'description': product.description,
        'base_price': str(product.base_price),
        'current_price': str(product.current_price),
        'discount_percentage': str(product.discount_percentage),
        'discount_start_date': product.discount_start_date,
        'discount_end_date': product.discount_end_date,
        'category': product.category,
        'created_at': product.created_at
    } for product in products])

@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'brand': openapi.Schema(type=openapi.TYPE_STRING),
            'description': openapi.Schema(type=openapi.TYPE_STRING),
            'base_price': openapi.Schema(type=openapi.TYPE_NUMBER),
            'category': openapi.Schema(type=openapi.TYPE_STRING),
            'discount_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
            'discount_start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'discount_end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        }
    )
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        fields = ['name', 'brand', 'description', 'base_price', 'category', 
                 'discount_percentage', 'discount_start_date', 'discount_end_date']
        for field in fields:
            if field in request.data:
                setattr(product, field, request.data[field])
        product.save()
        return Response({
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'description': product.description,
            'base_price': str(product.base_price),
            'current_price': str(product.current_price),
            'discount_percentage': str(product.discount_percentage),
            'discount_start_date': product.discount_start_date,
            'discount_end_date': product.discount_end_date,
            'category': product.category,
            'created_at': product.created_at
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

# Inventario
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['product_id', 'quantity'],
        properties={
            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    )
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_inventory(request):
    try:
        product = Product.objects.get(id=request.data['product_id'])
        inventory = Inventory.objects.create(
            product=product,
            quantity=request.data['quantity']
        )
        return Response({
            'id': inventory.id,
            'product_id': inventory.product.id,
            'quantity': inventory.quantity,
            'last_updated': inventory.last_updated
        }, status=status.HTTP_201_CREATED)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response('Inventario encontrado'),
        404: 'Inventario no encontrado'
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_inventory(request, product_id=None):
    # Log de la información de autenticación
    logger.debug(f"Headers de la solicitud: {request.headers}")
    logger.debug(f"Usuario autenticado: {request.user}")
    logger.debug(f"Auth: {request.auth}")
    
    if product_id:
        try:
            inventory = Inventory.objects.get(product_id=product_id)
            return Response({
                'id': inventory.id,
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'quantity': inventory.quantity,
                'last_updated': inventory.last_updated
            })
        except Inventory.DoesNotExist:
            logger.warning(f"Inventario no encontrado para el producto {product_id}")
            return Response({'error': 'Inventory not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        inventories = Inventory.objects.select_related('product').all()
        logger.info(f"Número de inventarios encontrados: {inventories.count()}")
        return Response([{
            'id': inventory.id,
            'product_id': inventory.product.id,
            'product_name': inventory.product.name,
            'quantity': inventory.quantity,
            'last_updated': inventory.last_updated
        } for inventory in inventories])

# Ratings
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['product_id', 'rating', 'review'],
        properties={
            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'rating': openapi.Schema(type=openapi.TYPE_INTEGER),
            'review': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_rating(request):
    try:
        product = Product.objects.get(id=request.data['product_id'])
        rating = Rating.objects.create(
            user=None,
            product=product,
            rating=request.data['rating'],
            review=request.data['review']
        )
        return Response({
            'id': rating.id,
            'user_id': None,
            'product_id': rating.product.id,
            'rating': rating.rating,
            'review': rating.review,
            'created_at': rating.created_at
        }, status=status.HTTP_201_CREATED)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_ratings(request, product_id):
    ratings = Rating.objects.filter(product_id=product_id)
    return Response([{
        'id': rating.id,
        'user_id': rating.user.id if rating.user else None,
        'product_id': rating.product.id,
        'rating': rating.rating,
        'review': rating.review,
        'created_at': rating.created_at
    } for rating in ratings])

@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request):
    recommendations = RecommendationService.get_recommendations()
    
    return Response({
        'highly_recommended': [{
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'price': str(product.price),
            'category': product.category
        } for product in recommendations['highly_recommended']],
        'recommended': [{
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'price': str(product.price),
            'category': product.category
        } for product in recommendations['recommended']],
        'not_recommended': [{
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'price': str(product.price),
            'category': product.category
        } for product in recommendations['not_recommended']]
    })

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['product_id', 'quantity'],
        properties={
            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    )
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_sale(request):
    try:
        product = Product.objects.get(id=request.data['product_id'])
        quantity = int(request.data['quantity'])
        
        # Verificar inventario
        inventory = product.inventory_set.first()
        if not inventory or inventory.quantity < quantity:
            return Response(
                {'error': 'No hay suficiente inventario'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear la venta
        sale = Sale.objects.create(
            user=None,
            product=product,
            quantity=quantity,
            unit_price=product.current_price
        )
        
        # Actualizar inventario
        inventory.quantity -= quantity
        inventory.save()
        
        return Response({
            'id': sale.id,
            'product_name': product.name,
            'quantity': sale.quantity,
            'unit_price': str(sale.unit_price),
            'total_amount': str(sale.total_amount),
            'sale_date': sale.sale_date
        }, status=status.HTTP_201_CREATED)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_sales(request):
    sales = Sale.objects.all()
    return Response([{
        'id': sale.id,
        'product_name': sale.product.name,
        'product_id': sale.product.id,
        'quantity': sale.quantity,
        'unit_price': str(sale.unit_price),
        'total_price': str(sale.total_price),
        'created_at': sale.created_at
    } for sale in sales])
