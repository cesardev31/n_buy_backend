from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from products.models import Product, Sale, Inventory
from django.db.models.functions import TruncMonth

@swagger_auto_schema(
    method='get',
    operation_description="Get general dashboard metrics",
    responses={
        200: openapi.Response(
            description="Metrics retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'last_month_sales': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'potential_losses': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'total_revenue': openapi.Schema(type=openapi.TYPE_NUMBER),
                }
            )
        ),
        401: openapi.Response(description="Unauthorized"),
        500: openapi.Response(description="Server error")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_metrics(request):
    try:
        # Get last month's date
        last_month = timezone.now() - timedelta(days=30)
        
        # Last month sales
        last_month_sales = Sale.objects.filter(
            created_at__gte=last_month
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Potential losses (out of stock products * price)
        potential_losses = Product.objects.filter(
            inventory__quantity=0
        ).aggregate(
            total=Sum('base_price')
        )['total'] or 0
        
        # Total revenue (all sales)
        total_revenue = Sale.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        return Response({
            'last_month_sales': float(last_month_sales),
            'potential_losses': float(potential_losses),
            'total_revenue': float(total_revenue)
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Get historical sales data by month",
    responses={
        200: openapi.Response(
            description="Historical data retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'history': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'date': openapi.Schema(type=openapi.TYPE_STRING),
                                'total_sales': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'sales_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    )
                }
            )
        ),
        401: openapi.Response(description="Unauthorized"),
        500: openapi.Response(description="Server error")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sales_history(request):
    try:
        # Get sales by month
        history = Sale.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_sales=Sum('total_price'),
            sales_count=Count('id')
        ).order_by('month')
        
        return Response({
            'history': [{
                'date': item['month'].strftime('%Y-%m'),
                'total_sales': float(item['total_sales']),
                'sales_count': item['sales_count']
            } for item in history]
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Get product distribution by category",
    responses={
        200: openapi.Response(
            description="Distribution retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'distribution': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'category': openapi.Schema(type=openapi.TYPE_STRING),
                                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'percentage': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        )
                    )
                }
            )
        ),
        401: openapi.Response(description="Unauthorized"),
        500: openapi.Response(description="Server error")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category_distribution(request):
    try:
        # Get total products
        total_products = Product.objects.count()
        
        # Get count by category
        distribution = Product.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Calculate percentages
        for item in distribution:
            item['percentage'] = (item['count'] / total_products) * 100
            
        return Response({
            'distribution': [{
                'category': item['category'],
                'count': item['count'],
                'percentage': item['percentage']
            } for item in distribution]
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
