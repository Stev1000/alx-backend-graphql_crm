# crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order


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


class Query(graphene.ObjectType):
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.Int())
    
    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.Int())
    
    # Order queries
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.Int())

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


# Mutations for creating/updating data
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)

    def mutate(self, info, name, email, phone=None):
        customer = Customer.objects.create(
            name=name,
            email=email,
            phone=phone
        )
        return CreateCustomer(customer=customer)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        product = Product.objects.create(
            name=name,
            price=price,
            stock=stock
        )
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.Int(required=True)
        product_ids = graphene.List(graphene.Int, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(pk=customer_id)
            order = Order.objects.create(customer=customer)
            
            products = Product.objects.filter(id__in=product_ids)
            order.products.set(products)
            order.calculate_total()  # Calculate total after adding products
            
            return CreateOrder(order=order)
        except Customer.DoesNotExist:
            raise Exception("Customer not found")


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
