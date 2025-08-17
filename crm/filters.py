import django_filters
from django.db.models import Q
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    # Case-insensitive partial match for name
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Case-insensitive partial match for email
    email = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters for created_at
    created_at_gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Custom filter for phone number pattern (starts with specific pattern)
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern')
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at_gte', 'created_at_lte', 'phone_pattern']
    
    def filter_phone_pattern(self, queryset, name, value):
        """Custom filter to match phone numbers that start with a specific pattern"""
        if value:
            return queryset.filter(phone__startswith=value)
        return queryset


class ProductFilter(django_filters.FilterSet):
    # Case-insensitive partial match for name
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Price range filters
    price_gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Stock filters
    stock = django_filters.NumberFilter(field_name='stock', lookup_expr='exact')
    stock_gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    
    # Low stock filter (stock < 10)
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    
    class Meta:
        model = Product
        fields = ['name', 'price_gte', 'price_lte', 'stock', 'stock_gte', 'stock_lte', 'low_stock']
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock (< 10)"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset


class OrderFilter(django_filters.FilterSet):
    # Total amount range filters
    total_amount_gte = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_amount_lte = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    
    # Order date range filters
    order_date_gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    order_date_lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Filter by customer name (related field lookup)
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains')
    
    # Filter by product name (related field lookup through many-to-many)
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains')
    
    # Filter orders that include a specific product ID
    product_id = django_filters.NumberFilter(field_name='products__id', lookup_expr='exact')
    
    class Meta:
        model = Order
        fields = [
            'total_amount_gte', 'total_amount_lte',
            'order_date_gte', 'order_date_lte',
            'customer_name', 'product_name', 'product_id'
        ]
