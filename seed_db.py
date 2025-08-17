import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql.settings")
django.setup()

from crm.models import Customer, Product, Order
from django.utils import timezone

print("🌱 Seeding database...")

# --- Customers ---
customers_data = [
    {"name": "Alice", "email": "alice@example.com", "phone": "123456789"},
    {"name": "Bob", "email": "bob@example.com", "phone": "987654321"},
    {"name": "Carol", "email": "carol@example.com", "phone": "555555555"},
]

customers = {}
for data in customers_data:
    customer, created = Customer.objects.get_or_create(
        email=data["email"], defaults=data
    )
    customers[data["name"]] = customer
    if created:
        print(f"✅ Created customer: {customer.name}")
    else:
        print(f"⚠️ Customer already exists: {customer.email}")

# --- Products ---
products_data = [
    {"name": "Laptop", "price": 1000.00, "stock": 10},
    {"name": "Phone", "price": 500.00, "stock": 20},
    {"name": "Headphones", "price": 100.00, "stock": 50},
]

products = {}
for data in products_data:
    product, created = Product.objects.get_or_create(
        name=data["name"], defaults=data
    )
    products[data["name"]] = product
    if created:
        print(f"✅ Created product: {product.name}")
    else:
        print(f"⚠️ Product already exists: {product.name}")

# --- Orders ---
try:
    # Create order for Alice
    order, created = Order.objects.get_or_create(
        customer=customers["Alice"],
        defaults={'order_date': timezone.now()}
    )
    
    if created:
        # Add products to the order
        order.products.add(products["Laptop"], products["Headphones"])
        
        # Calculate the total using the method
        order.calculate_total()
        
        print(f"✅ Created order for {order.customer.name}")
        print(f"   Products: {order.products.count()}")
        print(f"   Total: ${order.total_amount}")
    else:
        print(f"⚠️ Order already exists for {customers['Alice'].name}")

except Exception as e:
    print(f"❌ Failed to create order: {e}")

print("✨ Done seeding data!")
