import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from .models import Customer, Product, Order
import json
import re


# ================== TYPES ==================

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


# ================== HELPER FUNCTIONS ==================

def validate_email_format(email):
    """Validate email format"""
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def validate_phone_format(phone):
    """Validate phone format - basic validation"""
    if not phone:
        return True  # Phone is optional
    # Basic phone validation - adjust pattern as needed
    phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
    return bool(phone_pattern.match(phone.replace(' ', '').replace('-', '')))


def validate_price(price):
    """Validate price is positive"""
    return price is not None and price > 0


def validate_stock(stock):
    """Validate stock is non-negative"""
    return stock is not None and stock >= 0


# ================== QUERIES ==================

class Query(graphene.ObjectType):
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.Int(required=True))

    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.Int(required=True))

    # Order queries
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.Int(required=True))

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None

    def resolve_orders(self, info):
        return Order.objects.all()

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None


# ================== CUSTOMER MUTATIONS ==================

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Validate input
        if not name or not name.strip():
            return CreateCustomer(
                customer=None,
                success=False,
                message="Name is required and cannot be empty"
            )
        
        if not validate_email_format(email):
            return CreateCustomer(
                customer=None,
                success=False,
                message="Invalid email format"
            )
        
        if phone and not validate_phone_format(phone):
            return CreateCustomer(
                customer=None,
                success=False,
                message="Invalid phone format"
            )
        
        # Check for existing email
        if Customer.objects.filter(email=email.lower()).exists():
            return CreateCustomer(
                customer=None,
                success=False,
                message="Email already exists"
            )
        
        try:
            customer = Customer.objects.create(
                name=name.strip(),
                email=email.lower(),
                phone=phone.strip() if phone else None
            )
            return CreateCustomer(
                customer=customer,
                success=True,
                message="Customer created successfully"
            )
        except Exception as e:
            return CreateCustomer(
                customer=None,
                success=False,
                message=f"Error creating customer: {str(e)}"
            )


class UpdateCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String()
        email = graphene.String()
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, name=None, email=None, phone=None):
        try:
            customer = Customer.objects.get(pk=id)
            
            # Validate name if provided
            if name is not None and (not name or not name.strip()):
                return UpdateCustomer(
                    customer=None,
                    success=False,
                    message="Name cannot be empty"
                )
            
            # Validate email if provided
            if email is not None:
                if not validate_email_format(email):
                    return UpdateCustomer(
                        customer=None,
                        success=False,
                        message="Invalid email format"
                    )
                
                # Check email uniqueness (excluding current customer)
                if email.lower() != customer.email.lower() and Customer.objects.filter(email=email.lower()).exists():
                    return UpdateCustomer(
                        customer=None,
                        success=False,
                        message="Email already exists"
                    )
            
            # Validate phone if provided
            if phone is not None and phone and not validate_phone_format(phone):
                return UpdateCustomer(
                    customer=None,
                    success=False,
                    message="Invalid phone format"
                )
            
            # Update fields
            if name is not None:
                customer.name = name.strip()
            if email is not None:
                customer.email = email.lower()
            if phone is not None:
                customer.phone = phone.strip() if phone else None
            
            customer.save()
            return UpdateCustomer(
                customer=customer,
                success=True,
                message="Customer updated successfully"
            )
        except Customer.DoesNotExist:
            return UpdateCustomer(
                customer=None,
                success=False,
                message="Customer not found"
            )
        except Exception as e:
            return UpdateCustomer(
                customer=None,
                success=False,
                message=f"Error updating customer: {str(e)}"
            )


class DeleteCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            customer = Customer.objects.get(pk=id)
            
            # Check if customer has orders
            if customer.order_set.exists():
                return DeleteCustomer(
                    success=False,
                    message="Cannot delete customer with existing orders"
                )
            
            customer.delete()
            return DeleteCustomer(
                success=True,
                message="Customer deleted successfully"
            )
        except Customer.DoesNotExist:
            return DeleteCustomer(
                success=False,
                message="Customer not found"
            )
        except Exception as e:
            return DeleteCustomer(
                success=False,
                message=f"Error deleting customer: {str(e)}"
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(graphene.String, required=True)  # JSON strings

    customers = graphene.List(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        created_customers = []
        errors = []
        
        try:
            with transaction.atomic():
                for i, customer_data in enumerate(customers):
                    try:
                        data = json.loads(customer_data)
                        
                        # Validate required fields
                        if not data.get("name") or not data.get("email"):
                            errors.append(f"Customer {i+1}: Name and email are required")
                            continue
                        
                        # Validate email format
                        if not validate_email_format(data["email"]):
                            errors.append(f"Customer {i+1}: Invalid email format")
                            continue
                        
                        # Check for duplicate email
                        if Customer.objects.filter(email=data["email"].lower()).exists():
                            errors.append(f"Customer {i+1}: Email already exists")
                            continue
                        
                        # Validate phone if provided
                        phone = data.get("phone", "")
                        if phone and not validate_phone_format(phone):
                            errors.append(f"Customer {i+1}: Invalid phone format")
                            continue
                        
                        customer = Customer.objects.create(
                            name=data["name"].strip(),
                            email=data["email"].lower(),
                            phone=phone.strip() if phone else None
                        )
                        created_customers.append(customer)
                        
                    except json.JSONDecodeError:
                        errors.append(f"Customer {i+1}: Invalid JSON format")
                    except Exception as e:
                        errors.append(f"Customer {i+1}: {str(e)}")

            return BulkCreateCustomers(
                customers=created_customers,
                success=len(created_customers) > 0,
                message=f"Created {len(created_customers)} customers. {len(errors)} errors.",
                errors=errors
            )
        except Exception as e:
            return BulkCreateCustomers(
                customers=[],
                success=False,
                message=f"Bulk creation failed: {str(e)}",
                errors=[str(e)]
            )


# ================== PRODUCT MUTATIONS ==================

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, price, stock=0):
        # Validate input
        if not name or not name.strip():
            return CreateProduct(
                product=None,
                success=False,
                message="Product name is required and cannot be empty"
            )
        
        if not validate_price(price):
            return CreateProduct(
                product=None,
                success=False,
                message="Price must be greater than 0"
            )
        
        if not validate_stock(stock):
            return CreateProduct(
                product=None,
                success=False,
                message="Stock must be non-negative"
            )
        
        try:
            product = Product.objects.create(
                name=name.strip(),
                price=round(price, 2),
                stock=stock
            )
            return CreateProduct(
                product=product,
                success=True,
                message="Product created successfully"
            )
        except Exception as e:
            return CreateProduct(
                product=None,
                success=False,
                message=f"Error creating product: {str(e)}"
            )


class UpdateProduct(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String()
        price = graphene.Float()
        stock = graphene.Int()

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, name=None, price=None, stock=None):
        try:
            product = Product.objects.get(pk=id)
            
            # Validate name if provided
            if name is not None and (not name or not name.strip()):
                return UpdateProduct(
                    product=None,
                    success=False,
                    message="Product name cannot be empty"
                )
            
            # Validate price if provided
            if price is not None and not validate_price(price):
                return UpdateProduct(
                    product=None,
                    success=False,
                    message="Price must be greater than 0"
                )
            
            # Validate stock if provided
            if stock is not None and not validate_stock(stock):
                return UpdateProduct(
                    product=None,
                    success=False,
                    message="Stock must be non-negative"
                )
            
            # Update fields
            if name is not None:
                product.name = name.strip()
            if price is not None:
                product.price = round(price, 2)
            if stock is not None:
                product.stock = stock
            
            product.save()
            return UpdateProduct(
                product=product,
                success=True,
                message="Product updated successfully"
            )
        except Product.DoesNotExist:
            return UpdateProduct(
                product=None,
                success=False,
                message="Product not found"
            )
        except Exception as e:
            return UpdateProduct(
                product=None,
                success=False,
                message=f"Error updating product: {str(e)}"
            )


class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            product = Product.objects.get(pk=id)
            
            # Check if product is in any orders
            if product.order_set.exists():
                return DeleteProduct(
                    success=False,
                    message="Cannot delete product that exists in orders"
                )
            
            product.delete()
            return DeleteProduct(
                success=True,
                message="Product deleted successfully"
            )
        except Product.DoesNotExist:
            return DeleteProduct(
                success=False,
                message="Product not found"
            )
        except Exception as e:
            return DeleteProduct(
                success=False,
                message=f"Error deleting product: {str(e)}"
            )


class BulkCreateProducts(graphene.Mutation):
    class Arguments:
        products = graphene.List(graphene.String, required=True)  # JSON strings

    products = graphene.List(ProductType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, products):
        created_products = []
        errors = []
        
        try:
            with transaction.atomic():
                for i, product_data in enumerate(products):
                    try:
                        data = json.loads(product_data)
                        
                        # Validate required fields
                        if not data.get("name") or data.get("price") is None:
                            errors.append(f"Product {i+1}: Name and price are required")
                            continue
                        
                        # Validate price
                        if not validate_price(data["price"]):
                            errors.append(f"Product {i+1}: Price must be greater than 0")
                            continue
                        
                        # Validate stock
                        stock = data.get("stock", 0)
                        if not validate_stock(stock):
                            errors.append(f"Product {i+1}: Stock must be non-negative")
                            continue
                        
                        product = Product.objects.create(
                            name=data["name"].strip(),
                            price=round(data["price"], 2),
                            stock=stock
                        )
                        created_products.append(product)
                        
                    except json.JSONDecodeError:
                        errors.append(f"Product {i+1}: Invalid JSON format")
                    except Exception as e:
                        errors.append(f"Product {i+1}: {str(e)}")

            return BulkCreateProducts(
                products=created_products,
                success=len(created_products) > 0,
                message=f"Created {len(created_products)} products. {len(errors)} errors.",
                errors=errors
            )
        except Exception as e:
            return BulkCreateProducts(
                products=[],
                success=False,
                message=f"Bulk creation failed: {str(e)}",
                errors=[str(e)]
            )


class BulkUpdateProductStock(graphene.Mutation):
    class Arguments:
        updates = graphene.List(graphene.String, required=True)  # JSON strings

    products = graphene.List(ProductType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, updates):
        updated_products = []
        errors = []
        
        try:
            with transaction.atomic():
                for i, update_data in enumerate(updates):
                    try:
                        data = json.loads(update_data)
                        
                        # Validate required fields
                        if not data.get("id") or data.get("stock") is None:
                            errors.append(f"Update {i+1}: ID and stock are required")
                            continue
                        
                        # Validate stock
                        if not validate_stock(data["stock"]):
                            errors.append(f"Update {i+1}: Stock must be non-negative")
                            continue
                        
                        try:
                            product = Product.objects.get(pk=data["id"])
                            product.stock = data["stock"]
                            product.save()
                            updated_products.append(product)
                        except Product.DoesNotExist:
                            errors.append(f"Update {i+1}: Product not found")
                            
                    except json.JSONDecodeError:
                        errors.append(f"Update {i+1}: Invalid JSON format")
                    except Exception as e:
                        errors.append(f"Update {i+1}: {str(e)}")

            return BulkUpdateProductStock(
                products=updated_products,
                success=len(updated_products) > 0,
                message=f"Updated {len(updated_products)} products. {len(errors)} errors.",
                errors=errors
            )
        except Exception as e:
            return BulkUpdateProductStock(
                products=[],
                success=False,
                message=f"Bulk update failed: {str(e)}",
                errors=[str(e)]
            )


# ================== ORDER MUTATIONS ==================

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.Int(required=True)
        product_ids = graphene.List(graphene.Int, required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids):
        if not product_ids:
            return CreateOrder(
                order=None,
                success=False,
                message="At least one product is required"
            )
        
        try:
            # Verify customer exists
            customer = Customer.objects.get(pk=customer_id)
            
            # Verify all products exist
            products = Product.objects.filter(id__in=product_ids)
            if len(products) != len(product_ids):
                missing_ids = set(product_ids) - set(products.values_list('id', flat=True))
                return CreateOrder(
                    order=None,
                    success=False,
                    message=f"Products not found: {list(missing_ids)}"
                )
            
            # Check stock availability (assuming quantity = 1 for each product)
            out_of_stock = []
            for product in products:
                if product.stock <= 0:
                    out_of_stock.append(product.name)
            
            if out_of_stock:
                return CreateOrder(
                    order=None,
                    success=False,
                    message=f"Products out of stock: {', '.join(out_of_stock)}"
                )
            
            # Create order
            with transaction.atomic():
                order = Order.objects.create(customer=customer)
                order.products.set(products)
                
                # Calculate and save total
                total = sum(product.price for product in products)
                order.total = total
                order.save()
                
                # Update stock (decrease by 1 for each product)
                for product in products:
                    product.stock -= 1
                    product.save()
            
            return CreateOrder(
                order=order,
                success=True,
                message="Order created successfully"
            )
        except Customer.DoesNotExist:
            return CreateOrder(
                order=None,
                success=False,
                message="Customer not found"
            )
        except Exception as e:
            return CreateOrder(
                order=None,
                success=False,
                message=f"Error creating order: {str(e)}"
            )


class UpdateOrder(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        customer_id = graphene.Int()
        product_ids = graphene.List(graphene.Int)
        add_product_ids = graphene.List(graphene.Int)
        remove_product_ids = graphene.List(graphene.Int)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, customer_id=None, product_ids=None, add_product_ids=None, remove_product_ids=None):
        try:
            order = Order.objects.get(pk=id)
            
            with transaction.atomic():
                # Update customer if provided
                if customer_id:
                    try:
                        customer = Customer.objects.get(pk=customer_id)
                        order.customer = customer
                    except Customer.DoesNotExist:
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message="Customer not found"
                        )
                
                # Replace all products if product_ids provided
                if product_ids is not None:
                    if not product_ids:
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message="At least one product is required"
                        )
                    
                    products = Product.objects.filter(id__in=product_ids)
                    if len(products) != len(product_ids):
                        missing_ids = set(product_ids) - set(products.values_list('id', flat=True))
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message=f"Products not found: {list(missing_ids)}"
                        )
                    
                    # Restore stock for current products
                    for product in order.products.all():
                        product.stock += 1
                        product.save()
                    
                    # Check stock for new products
                    out_of_stock = []
                    for product in products:
                        if product.stock <= 0:
                            out_of_stock.append(product.name)
                    
                    if out_of_stock:
                        # Restore original products stock
                        for product in order.products.all():
                            product.stock -= 1
                            product.save()
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message=f"Products out of stock: {', '.join(out_of_stock)}"
                        )
                    
                    # Set new products and update stock
                    order.products.set(products)
                    for product in products:
                        product.stock -= 1
                        product.save()
                
                # Add products if add_product_ids provided
                if add_product_ids:
                    add_products = Product.objects.filter(id__in=add_product_ids)
                    if len(add_products) != len(add_product_ids):
                        missing_ids = set(add_product_ids) - set(add_products.values_list('id', flat=True))
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message=f"Products to add not found: {list(missing_ids)}"
                        )
                    
                    # Check stock
                    out_of_stock = []
                    for product in add_products:
                        if product.stock <= 0:
                            out_of_stock.append(product.name)
                    
                    if out_of_stock:
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message=f"Products out of stock: {', '.join(out_of_stock)}"
                        )
                    
                    order.products.add(*add_products)
                    for product in add_products:
                        product.stock -= 1
                        product.save()
                
                # Remove products if remove_product_ids provided
                if remove_product_ids:
                    remove_products = Product.objects.filter(id__in=remove_product_ids)
                    
                    # Check if removing all products would leave order empty
                    remaining_count = order.products.count() - len(remove_products)
                    if remaining_count <= 0:
                        return UpdateOrder(
                            order=None,
                            success=False,
                            message="Cannot remove all products from order"
                        )
                    
                    order.products.remove(*remove_products)
                    # Restore stock for removed products
                    for product in remove_products:
                        product.stock += 1
                        product.save()
                
                # Recalculate total
                total = sum(product.price for product in order.products.all())
                order.total = total
                order.save()
            
            return UpdateOrder(
                order=order,
                success=True,
                message="Order updated successfully"
            )
        except Order.DoesNotExist:
            return UpdateOrder(
                order=None,
                success=False,
                message="Order not found"
            )
        except Exception as e:
            return UpdateOrder(
                order=None,
                success=False,
                message=f"Error updating order: {str(e)}"
            )


class DeleteOrder(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            order = Order.objects.get(pk=id)
            
            # Restore stock for all products in the order
            with transaction.atomic():
                for product in order.products.all():
                    product.stock += 1
                    product.save()
                
                order.delete()
            
            return DeleteOrder(
                success=True,
                message="Order deleted successfully"
            )
        except Order.DoesNotExist:
            return DeleteOrder(
                success=False,
                message="Order not found"
            )
        except Exception as e:
            return DeleteOrder(
                success=False,
                message=f"Error deleting order: {str(e)}"
            )


# ================== ROOT MUTATION ==================

class Mutation(graphene.ObjectType):
    # Customers
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()

    # Products
    create_product = CreateProduct.Field()
    bulk_create_products = BulkCreateProducts.Field()
    bulk_update_product_stock = BulkUpdateProductStock.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()

    # Orders
    create_order = CreateOrder.Field()
    update_order = UpdateOrder.Field()
    delete_order = DeleteOrder.Field()


# ================== SCHEMA ==================

schema = graphene.Schema(query=Query, mutation=Mutation)
