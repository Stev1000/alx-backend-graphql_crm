# crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from .models import Customer, Product, Order


# =================== TYPES ===================

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


# =================== QUERY ===================

class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.Int(required=True))
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.Int(required=True))
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


# =================== CUSTOMER MUTATIONS ===================

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        try:
            customer = Customer.objects.create(name=name, email=email, phone=phone)
            return CreateCustomer(customer=customer, success=True, message="Customer created successfully")
        except Exception as e:
            return CreateCustomer(customer=None, success=False, message=str(e))


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
            if name is not None:
                customer.name = name
            if email is not None:
                customer.email = email
            if phone is not None:
                customer.phone = phone
            customer.save()
            return UpdateCustomer(customer=customer, success=True, message="Customer updated successfully")
        except Customer.DoesNotExist:
            return UpdateCustomer(customer=None, success=False, message="Customer not found")
        except Exception as e:
            return UpdateCustomer(customer=None, success=False, message=str(e))


class DeleteCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            customer = Customer.objects.get(pk=id)
            customer.delete()
            return DeleteCustomer(success=True, message="Customer deleted successfully")
        except Customer.DoesNotExist:
            return DeleteCustomer(success=False, message="Customer not found")


# =================== PRODUCT MUTATIONS ===================

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, price, stock=0):
        try:
            product = Product.objects.create(name=name, price=price, stock=stock)
            return CreateProduct(product=product, success=True, message="Product created successfully")
        except Exception as e:
            return CreateProduct(product=None, success=False, message=str(e))


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
            if name is not None:
                product.name = name
            if price is not None:
                product.price = price
            if stock is not None:
                product.stock = stock
            product.save()
            return UpdateProduct(product=product, success=True, message="Product updated successfully")
        except Product.DoesNotExist:
            return UpdateProduct(product=None, success=False, message="Product not found")
        except Exception as e:
            return UpdateProduct(product=None, success=False, message=str(e))


class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            product = Product.objects.get(pk=id)
            product.delete()
            return DeleteProduct(success=True, message="Product deleted successfully")
        except Product.DoesNotExist:
            return DeleteProduct(success=False, message="Product not found")


# =================== ORDER MUTATIONS ===================

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.Int(required=True)
        product_ids = graphene.List(graphene.Int, required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids):
        if not product_ids:
            return CreateOrder(order=None, success=False, message="At least one product is required")
        try:
            customer = Customer.objects.get(pk=customer_id)
            products = Product.objects.filter(id__in=product_ids)
            if len(products) != len(product_ids):
                missing_ids = set(product_ids) - set(products.values_list('id', flat=True))
                return CreateOrder(order=None, success=False, message=f"Products not found: {list(missing_ids)}")

            out_of_stock = [p.name for p in products if p.stock <= 0]
            if out_of_stock:
                return CreateOrder(order=None, success=False, message=f"Products out of stock: {', '.join(out_of_stock)}")

            with transaction.atomic():
                order = Order.objects.create(customer=customer)
                order.products.set(products)
                order.total = sum(p.price for p in products)
                order.save()
                for product in products:
                    product.stock -= 1
                    product.save()

            return CreateOrder(order=order, success=True, message="Order created successfully")

        except Customer.DoesNotExist:
            return CreateOrder(order=None, success=False, message="Customer not found")
        except Exception as e:
            return CreateOrder(order=None, success=False, message=f"Error creating order: {str(e)}")


class UpdateOrder(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        customer_id = graphene.Int()
        product_ids = graphene.List(graphene.Int)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, customer_id=None, product_ids=None):
        try:
            order = Order.objects.get(pk=id)
            if customer_id:
                customer = Customer.objects.get(pk=customer_id)
                order.customer = customer
            if product_ids is not None:
                products = Product.objects.filter(id__in=product_ids)
                order.products.set(products)
            order.total = sum(p.price for p in order.products.all())
            order.save()
            return UpdateOrder(order=order, success=True, message="Order updated successfully")
        except Order.DoesNotExist:
            return UpdateOrder(order=None, success=False, message="Order not found")
        except Customer.DoesNotExist:
            return UpdateOrder(order=None, success=False, message="Customer not found")
        except Exception as e:
            return UpdateOrder(order=None, success=False, message=str(e))


class DeleteOrder(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            order = Order.objects.get(pk=id)
            order.delete()
            return DeleteOrder(success=True, message="Order deleted successfully")
        except Order.DoesNotExist:
            return DeleteOrder(success=False, message="Order not found")


# =================== BULK OPERATIONS ===================

class BulkCreateProducts(graphene.Mutation):
    class Arguments:
        products = graphene.List(graphene.JSONString, required=True)

    products = graphene.List(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, products):
        created_products = []
        try:
            for data in products:
                product = Product.objects.create(
                    name=data.get('name'),
                    price=data.get('price'),
                    stock=data.get('stock', 0)
                )
                created_products.append(product)
            return BulkCreateProducts(products=created_products, success=True,
                                      message=f"Created {len(created_products)} products")
        except Exception as e:
            return BulkCreateProducts(products=[], success=False, message=str(e))


class BulkUpdateProductStock(graphene.Mutation):
    class Arguments:
        updates = graphene.List(graphene.JSONString, required=True)

    products = graphene.List(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, updates):
        updated_products = []
        try:
            for data in updates:
                product = Product.objects.get(pk=data.get('id'))
                product.stock = data.get('stock')
                product.save()
                updated_products.append(product)
            return BulkUpdateProductStock(products=updated_products, success=True,
                                          message=f"Updated {len(updated_products)} products")
        except Exception as e:
            return BulkUpdateProductStock(products=[], success=False, message=str(e))


# =================== ROOT MUTATION ===================

class Mutation(graphene.ObjectType):
    # Customer mutations
    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()

    # Product mutations
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()

    # Order mutations
    create_order = CreateOrder.Field()
    update_order = UpdateOrder.Field()
    delete_order = DeleteOrder.Field()

    # Bulk operations
    bulk_create_products = BulkCreateProducts.Field()
    bulk_update_product_stock = BulkUpdateProductStock.Field()


# =================== SCHEMA ===================

schema = graphene.Schema(query=Query, mutation=Mutation)
