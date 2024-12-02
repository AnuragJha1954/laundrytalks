from django.urls import path
from .views import (
    get_all_categories,
    get_products_by_outlet,
    get_customer_by_phone_number,
    add_customer,
    place_order,
    get_orders_by_outlet,
    add_product
)

urlpatterns = [
    # Categories
    path('categories/', get_all_categories, name='get_all_categories'),

    # Products
    path('get-products/<int:outlet_id>/', get_products_by_outlet, name='get_products_by_outlet'),
    
    # Method to add a single product to the outlet
    path('<int:outlet_id>/product/add/', add_product, name='add_product_to_outlet'),
    
    # Customers
    path('get-customers/<int:outlet_id>/', get_customer_by_phone_number, name='get_customer_by_outlet_and_phone'),
    path('<int:outlet_id>/customers/add/', add_customer, name='add_customer_to_outlet'),

    # Orders
    path('<int:outlet_id>/orders/place/', place_order, name='place_order'),
    path('<int:outlet_id>/orders/', get_orders_by_outlet, name='get_orders_by_outlet'),
]
