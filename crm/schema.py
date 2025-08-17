import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# ---------------- GraphQL Types ----------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# ---------------- Queries ----------------
class Query(graphene.ObjectType):
    customer = graphene.relay.Node.Field(CustomerType)
    all_customers = DjangoFilterConnectionField(CustomerType)

    product = graphene.relay.Node.Field(ProductType)
    all_products = DjangoFilterConnectionField(ProductType)

    order = graphene.relay.Node.Field(OrderType)
    all_orders = DjangoFilterConnectionField(OrderType)


# ---------------- Mutations ----------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)

    customer = graphene.Field(CustomerType)

    def mutate(self, info, name, email, phone):
        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer)


class UpdateCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        email = graphene.String()
        phone = graphene.String()

    customer = graphene.Field(CustomerType)

    def mutate(self, info, id, name=None, email=None, phone=None):
        customer = Customer.objects.get(pk=id)
        if name:
            customer.name = name
        if email:
            customer.email = email
        if phone:
            customer.phone = phone
        customer.save()
        return UpdateCustomer(customer=customer)


class DeleteCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        customer = Customer.objects.get(pk=id)
        customer.delete()
        return DeleteCustomer(success=True)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price):
        product = Product.objects.create(name=name, price=price)
        return CreateProduct(product=product)


class UpdateProduct(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        price = graphene.Float()

    product = graphene.Field(ProductType)

    def mutate(self, info, id, name=None, price=None):
        product = Product.objects.get(pk=id)
        if name:
            product.name = name
        if price is not None:
            product.price = price
        product.save()
        return UpdateProduct(product=product)


class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        product = Product.objects.get(pk=id)
        product.delete()
        return DeleteProduct(success=True)


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_id, quantity):
        customer = Customer.objects.get(pk=customer_id)
        product = Product.objects.get(pk=product_id)
        order = Order.objects.create(customer=customer, quantity=quantity)
        order.products.add(product)  # ✅ ManyToMany handled properly
        return CreateOrder(order=order)


class UpdateOrder(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        quantity = graphene.Int()

    order = graphene.Field(OrderType)

    def mutate(self, info, id, quantity=None):
        order = Order.objects.get(pk=id)
        if quantity is not None:
            order.quantity = quantity
        order.save()
        return UpdateOrder(order=order)


class DeleteOrder(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        order = Order.objects.get(pk=id)
        order.delete()
        return DeleteOrder(success=True)


# ---------------- Root Mutation ----------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()

    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()

    create_order = CreateOrder.Field()
    update_order = UpdateOrder.Field()
    delete_order = DeleteOrder.Field()


# ---------------- Schema ----------------
schema = graphene.Schema(query=Query, mutation=Mutation)
