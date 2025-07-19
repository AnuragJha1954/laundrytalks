from django.urls import path
from . import views

urlpatterns = [
    # Method to create an outlet
    path('create_outlet/<int:user_id>/', views.create_outlet, name='create_outlet'),

    # Method to get all outlets
    path('get_all_outlets/', views.get_all_outlets, name='get_all_outlets'),

    # Method to add a product (via Excel file upload)
    path('add_products_excel/<int:user_id>/', views.add_products_excel, name='add_products_from_excel'),

    # Method to add a single product to the outlet
    path('add_product/<int:user_id>/<int:outlet_id>/', views.add_product, name='add_product_to_outlet'),

    # Method to create/update outlet creds
    path('manage_outlet_creds/<int:outlet_id>/<int:user_id>/', views.manage_outlet_creds, name='create_or_update_outlet_creds'),

    # Method to get outlet creds
    path('get_outlet_creds/<int:outlet_id>/', views.get_outlet_creds, name='get_outlet_creds'),

    # Method to get products for an outlet
    path('get_products_for_outlet/<int:outlet_id>/', views.get_products_for_outlet, name='get_products_for_outlet'),
    
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    
    # Method to get orders for an outlet
    path('<int:outlet_id>/get-orders/', views.get_orders_by_outlet, name='get_orders_by_outlet'),
    
    path('orders/invoice/<str:invoice_number>/', views.get_order_details_by_invoice, name='get-order-by-invoice'),
    
    path('generate-bill/<str:order_number>/', views.generate_bill, name='generate_bill'),
    
    path('orders/invoice/<str:invoice_number>/cancel/', views.cancel_order, name='cancel-order'),
    
    path('orders/invoice/<str:invoice_number>/refund/', views.add_refund, name='add-refund'),
    
    path('edit-bill/<int:outlet_id>/<str:order_number>/<int:user_id>/', views.update_order_discount, name='update_order_discount'),
    
    path('<int:outlet_id>/customers/', views.get_customers_by_outlet, name='get_customers_by_outlet'),
    
    path('customers/<int:customer_id>/edit/', views.edit_customer, name='edit_customer'),
    
]
