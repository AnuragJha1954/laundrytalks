from django.urls import path
from .views import (
    get_all_categories,
    get_products_by_outlet,
    get_customer_by_phone_number,
    add_customer,
    place_order,
    get_orders_by_outlet,
    add_product,
    brand_list_create,
    pattern_list_create,
    stain_type_list_create,
    defect_type_list_create,
    material_type_list_create,
    starch_type_list_create,
    detergent_type_list_create,
    detergent_scent_type_list_create,
    wash_temperature_type_list_create,
    fabric_softener_type_list_create,
    colour_list_create,
    topup_service_list_create,
    # invoice_view
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
    
    
    # path('test/', invoice_view, name='invoice'),
    
    # Specifiacations models endpoints
    path("brands/", brand_list_create, name="brand-list-create"),
    path("patterns/", pattern_list_create, name="pattern-list-create"),
    path("stain-types/", stain_type_list_create, name="stain-type-list-create"),
    path("defect-types/", defect_type_list_create, name="defect-type-list-create"),
    path("material-types/", material_type_list_create, name="material-type-list-create"),
    path("starch-types/", starch_type_list_create, name="starch-type-list-create"),
    path("detergent-types/", detergent_type_list_create, name="detergent-type-list-create"),
    path("detergent-scent-types/", detergent_scent_type_list_create, name="detergent-scent-type-list-create"),
    path("wash-temperature-types/", wash_temperature_type_list_create, name="wash-temperature-type-list-create"),
    path("fabric-softener-types/", fabric_softener_type_list_create, name="fabric-softener-type-list-create"),
    path("colours/", colour_list_create, name="colour-list-create"),
    path("topup-services/", topup_service_list_create, name="topup-service-list-create"),
]
