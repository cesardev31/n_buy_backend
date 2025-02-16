from django.core.management.base import BaseCommand
from django.utils import timezone
from products.models import Product, Sale
from users.models import User
from datetime import timedelta
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Generate sample sales data for the last 6 months'

    def handle(self, *args, **kwargs):
        # Get all products and users
        products = list(Product.objects.all())
        users = list(User.objects.all())

        if not products:
            self.stdout.write(self.style.ERROR('No products found. Please create some products first.'))
            return

        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create some users first.'))
            return

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=180)  # 6 months

        # Generate sales
        sales_count = 0
        current_date = start_date

        while current_date <= end_date:
            # Generate 3-10 sales per day
            daily_sales = random.randint(3, 10)
            
            for _ in range(daily_sales):
                product = random.choice(products)
                user = random.choice(users)
                quantity = random.randint(1, 5)
                
                # Calculate prices
                unit_price = product.current_price
                total_price = unit_price * Decimal(quantity)

                # Create sale
                Sale.objects.create(
                    user=user,
                    product=product,
                    unit_price=unit_price,
                    quantity=quantity,
                    total_price=total_price,
                    created_at=current_date + timedelta(
                        hours=random.randint(8, 20),  # Business hours
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59)
                    )
                )
                sales_count += 1

            current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {sales_count} sales records over the last 6 months')
        )
