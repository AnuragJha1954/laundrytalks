from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import (
    Outlet,
    Product,
    OutletCreds,
    Order,
    OrderItem,
    Customer
)

User = get_user_model()

class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = ['id', 'owner_name', 'company_owned', 'location', 'address', 'owner_details']
        read_only_fields = ['id']





class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['item_name', 'rate_per_unit', 'hsn_sac_code', 'category']  # Keep the category key
        ref_name = "PanelAPI_ProductSerializer"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Replace the 'category' field with the category name
        representation['category'] = instance.category.name
        return representation

    def validate(self, data):
        if not data.get('item_name'):
            raise ValidationError("Item name is required.")
        if not data.get('rate_per_unit'):
            raise ValidationError("Rate per unit is required.")
        if not data.get('category'):
            raise ValidationError("Category is required.")
        return data






class OutletCredsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutletCreds
        fields = ['username', 'password', 'user', 'outlet', 'email']
        depth =  1

    def validate(self, data):
        # Ensure the password meets the criteria
        if len(data['password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return data









class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number', 'state', 'gst_number', 'outlet','reference']  # Include 'outlet' as a field

    def validate(self, data):
        if not data.get('name'):
            raise serializers.ValidationError("Name is required.")
        if not data.get('phone_number'):
            raise serializers.ValidationError("Phone number is required.")
        if not data.get('state'):
            raise serializers.ValidationError("State is required.")
        return data






class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'total']

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    order_items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'order_number',
            'outlet',
            'customer',
            'date_of_billing',
            'invoice_number',
            'date_of_collection',
            'total_amount',
            'discount_percentage',
            'total_gst',
            'total_cgst',
            'total_sgst',
            'total_igst',
            'mode_of_payment',
            'order_items',
        ]






