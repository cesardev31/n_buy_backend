import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'n_buy_backend.settings')
django.setup()

from django.utils import timezone
from users.models import User
from products.models import Product, Inventory, Sale, Rating

def create_sample_data():
    # Crear productos
    products_data = [
        {
            'name': 'Laptop Gaming Pro',
            'brand': 'TechMaster',
            'description': 'Laptop gaming de alta gama con RTX 4080',
            'base_price': Decimal('1299.99'),
            'category': 'Computadoras',
            'discount_percentage': Decimal('10.00'),
        },
        {
            'name': 'Smartphone X12',
            'brand': 'SmartTech',
            'description': 'Smartphone de última generación',
            'base_price': Decimal('799.99'),
            'category': 'Móviles',
            'discount_percentage': Decimal('5.00'),
        },
        {
            'name': 'Monitor 4K Ultra',
            'brand': 'ViewPro',
            'description': 'Monitor 4K de 32 pulgadas',
            'base_price': Decimal('499.99'),
            'category': 'Monitores',
            'discount_percentage': Decimal('15.00'),
        },
        {
            'name': 'Teclado Mecánico RGB',
            'brand': 'GameMaster',
            'description': 'Teclado mecánico para gaming',
            'base_price': Decimal('129.99'),
            'category': 'Periféricos',
            'discount_percentage': Decimal('0.00'),
        },
        {
            'name': 'Mouse Gaming Pro',
            'brand': 'GameMaster',
            'description': 'Mouse gaming de alta precisión',
            'base_price': Decimal('79.99'),
            'category': 'Periféricos',
            'discount_percentage': Decimal('0.00'),
        },
        # Nuevos productos
        # Computadoras y Laptops
        {
            'name': 'Laptop Ultrabook Pro',
            'brand': 'TechMaster',
            'description': 'Laptop ultradelgada para profesionales',
            'base_price': Decimal('1099.99'),
            'category': 'Computadoras',
            'discount_percentage': Decimal('5.00'),
        },
        {
            'name': 'PC Gaming Ultimate',
            'brand': 'GameForce',
            'description': 'PC Gaming con RTX 4090 y Ryzen 9',
            'base_price': Decimal('2499.99'),
            'category': 'Computadoras',
            'discount_percentage': Decimal('0.00'),
        },
        {
            'name': 'Mini PC Office',
            'brand': 'TechMaster',
            'description': 'Mini PC para oficina y trabajo',
            'base_price': Decimal('399.99'),
            'category': 'Computadoras',
            'discount_percentage': Decimal('15.00'),
        },
        # Smartphones y Tablets
        {
            'name': 'Tablet Pro 12',
            'brand': 'SmartTech',
            'description': 'Tablet profesional de 12 pulgadas',
            'base_price': Decimal('699.99'),
            'category': 'Tablets',
            'discount_percentage': Decimal('10.00'),
        },
        {
            'name': 'Smartphone Lite',
            'brand': 'SmartTech',
            'description': 'Smartphone económico y eficiente',
            'base_price': Decimal('299.99'),
            'category': 'Móviles',
            'discount_percentage': Decimal('20.00'),
        },
        # Monitores
        {
            'name': 'Monitor Gaming 240Hz',
            'brand': 'ViewPro',
            'description': 'Monitor gaming de alta frecuencia',
            'base_price': Decimal('449.99'),
            'category': 'Monitores',
            'discount_percentage': Decimal('5.00'),
        },
        {
            'name': 'Monitor Ultrawide',
            'brand': 'ViewPro',
            'description': 'Monitor ultrawide de 34 pulgadas',
            'base_price': Decimal('599.99'),
            'category': 'Monitores',
            'discount_percentage': Decimal('10.00'),
        },
        # Periféricos
        {
            'name': 'Auriculares Gaming 7.1',
            'brand': 'GameMaster',
            'description': 'Auriculares gaming con sonido envolvente',
            'base_price': Decimal('149.99'),
            'category': 'Periféricos',
            'discount_percentage': Decimal('15.00'),
        },
        {
            'name': 'Webcam 4K Pro',
            'brand': 'ViewPro',
            'description': 'Webcam profesional 4K',
            'base_price': Decimal('199.99'),
            'category': 'Periféricos',
            'discount_percentage': Decimal('0.00'),
        },
        # Almacenamiento
        {
            'name': 'SSD 2TB NVMe',
            'brand': 'StoragePro',
            'description': 'Disco SSD NVMe de alta velocidad',
            'base_price': Decimal('249.99'),
            'category': 'Almacenamiento',
            'discount_percentage': Decimal('10.00'),
        },
        {
            'name': 'HDD 8TB',
            'brand': 'StoragePro',
            'description': 'Disco duro de alta capacidad',
            'base_price': Decimal('199.99'),
            'category': 'Almacenamiento',
            'discount_percentage': Decimal('5.00'),
        },
        # Redes
        {
            'name': 'Router Gaming Pro',
            'brand': 'NetMaster',
            'description': 'Router gaming de alta velocidad',
            'base_price': Decimal('299.99'),
            'category': 'Redes',
            'discount_percentage': Decimal('0.00'),
        },
        {
            'name': 'Switch 24 Puertos',
            'brand': 'NetMaster',
            'description': 'Switch gigabit de 24 puertos',
            'base_price': Decimal('179.99'),
            'category': 'Redes',
            'discount_percentage': Decimal('15.00'),
        },
        # Impresoras
        {
            'name': 'Impresora Láser Pro',
            'brand': 'PrintMaster',
            'description': 'Impresora láser profesional',
            'base_price': Decimal('399.99'),
            'category': 'Impresoras',
            'discount_percentage': Decimal('10.00'),
        },
        {
            'name': 'Impresora 3D',
            'brand': 'PrintMaster',
            'description': 'Impresora 3D de alta precisión',
            'base_price': Decimal('599.99'),
            'category': 'Impresoras',
            'discount_percentage': Decimal('0.00'),
        },
        # Software
        {
            'name': 'Antivirus Premium',
            'brand': 'SecureNet',
            'description': 'Software antivirus premium',
            'base_price': Decimal('79.99'),
            'category': 'Software',
            'discount_percentage': Decimal('25.00'),
        },
        {
            'name': 'Suite Office Pro',
            'brand': 'SoftMaster',
            'description': 'Suite de oficina profesional',
            'base_price': Decimal('149.99'),
            'category': 'Software',
            'discount_percentage': Decimal('20.00'),
        },
        # Componentes
        {
            'name': 'Tarjeta Gráfica RTX 4070',
            'brand': 'TechForce',
            'description': 'GPU gaming de alta gama',
            'base_price': Decimal('799.99'),
            'category': 'Componentes',
            'discount_percentage': Decimal('5.00'),
        },
        {
            'name': 'Procesador Ryzen 9',
            'brand': 'TechForce',
            'description': 'Procesador de alto rendimiento',
            'base_price': Decimal('599.99'),
            'category': 'Componentes',
            'discount_percentage': Decimal('0.00'),
        },
        # Gaming
        {
            'name': 'Silla Gaming Pro',
            'brand': 'GameMaster',
            'description': 'Silla ergonómica para gaming',
            'base_price': Decimal('299.99'),
            'category': 'Gaming',
            'discount_percentage': Decimal('15.00'),
        },
        {
            'name': 'Mesa Gaming RGB',
            'brand': 'GameMaster',
            'description': 'Mesa gaming con iluminación RGB',
            'base_price': Decimal('249.99'),
            'category': 'Gaming',
            'discount_percentage': Decimal('10.00'),
        },
        # Accesorios
        {
            'name': 'Mochila Laptop Pro',
            'brand': 'TechGear',
            'description': 'Mochila para laptop con protección',
            'base_price': Decimal('79.99'),
            'category': 'Accesorios',
            'discount_percentage': Decimal('20.00'),
        },
        {
            'name': 'Hub USB-C 12-en-1',
            'brand': 'TechGear',
            'description': 'Hub USB-C multifunción',
            'base_price': Decimal('89.99'),
            'category': 'Accesorios',
            'discount_percentage': Decimal('5.00'),
        },
        # Servidores
        {
            'name': 'Servidor NAS 4 Bahías',
            'brand': 'StoragePro',
            'description': 'Servidor NAS para almacenamiento en red',
            'base_price': Decimal('499.99'),
            'category': 'Servidores',
            'discount_percentage': Decimal('0.00'),
        },
        {
            'name': 'Servidor Rack 2U',
            'brand': 'TechMaster',
            'description': 'Servidor empresarial en rack',
            'base_price': Decimal('1999.99'),
            'category': 'Servidores',
            'discount_percentage': Decimal('10.00'),
        },
        # Seguridad
        {
            'name': 'Cámara IP 4K',
            'brand': 'SecureNet',
            'description': 'Cámara de seguridad IP 4K',
            'base_price': Decimal('199.99'),
            'category': 'Seguridad',
            'discount_percentage': Decimal('15.00'),
        },
        {
            'name': 'Sistema Alarma WiFi',
            'brand': 'SecureNet',
            'description': 'Sistema de alarma inteligente',
            'base_price': Decimal('299.99'),
            'category': 'Seguridad',
            'discount_percentage': Decimal('5.00'),
        },
    ]

    print("Creando productos...")
    products = []
    for product_data in products_data:
        try:
            product = Product.objects.create(**product_data)
            products.append(product)
            print(f"Producto creado: {product.name}")

            # Crear inventario para cada producto
            inventory = Inventory.objects.create(
                product=product,
                quantity=random.randint(10, 100)
            )
            print(f"Inventario creado para {product.name}: {inventory.quantity} unidades")
        except Exception as e:
            print(f"Error al crear producto {product_data['name']}: {str(e)}")

    # Crear ventas de muestra
    print("\nCreando ventas de muestra...")
    
    # Fechas para las ventas (últimos 30 días)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Crear entre 50 y 100 ventas aleatorias
    num_sales = random.randint(50, 100)
    for _ in range(num_sales):
        # Seleccionar un producto aleatorio
        product = random.choice(products)
        
        # Generar una fecha aleatoria en los últimos 30 días
        sale_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        
        # Cantidad aleatoria entre 1 y 5 unidades
        quantity = random.randint(1, 5)
        
        # Crear la venta
        sale = Sale.objects.create(
            product=product,
            quantity=quantity,
            unit_price=product.current_price,
            total_price=product.current_price * quantity,
            created_at=sale_date
        )
        print(f"Venta creada: {quantity} unidades de {product.name} por ${sale.total_price}")

    print("\nCreación de datos de ejemplo completada!")

if __name__ == '__main__':
    print("Iniciando creación de datos de ejemplo...")
    create_sample_data()
