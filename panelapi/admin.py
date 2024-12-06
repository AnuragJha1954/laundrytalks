from django.contrib import admin
from .models import (
    Outlet,
    Product,
    OutletCreds,
    Customer,
    Order,
    OrderItem,
    Category
)



@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ('owner_name', 'company_owned', 'location', 'address')
    search_fields = ('owner_name', 'company_owned', 'location')
    list_filter = ('location',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'rate_per_unit', 'hsn_sac_code')
    search_fields = ('item_name', 'hsn_sac_code')
    list_filter = ('outlets',)
    filter_horizontal = ('outlets',)  # For managing many-to-many relationships in the admin


@admin.register(OutletCreds)
class OutletCredsAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'outlet')
    search_fields = ('username', 'user__username', 'outlet__owner_name')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'state', 'gst_number','address')
    search_fields = ('name', 'phone_number', 'state')
    list_filter = ('state',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'outlet', 'customer', 'date_of_billing', 'total_amount')
    search_fields = ('order_number', 'invoice_number', 'outlet__owner_name', 'customer__name')
    list_filter = ('date_of_billing', 'outlet')
    date_hierarchy = 'date_of_billing'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'total')
    search_fields = ('order__order_number', 'product__item_name')
    list_filter = ('order__date_of_billing', 'product')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Display the ID and name in the admin list view
    search_fields = ('name',)     # Add search functionality for the name field
    ordering = ('name',)          # Order categories alphabetically by name
    list_per_page = 25            # Paginate the list view with 25 items per page