from rest_framework import serializers
from panelapi.models import (
    Category,
    Product,
    Customer,
    Order,
    OrderItem
)




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']  # Return category id and name





class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name')  # Get the category name, not the ID

    class Meta:
        model = Product
        fields = ['item_name', 'rate_per_unit', 'hsn_sac_code', 'category_name']  # Include category_name
        ref_name = "CounterAPI_ProductSerializer"    
    
    
        
        




class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number', 'state', 'gst_number', 'outlet']  # Include 'outlet' as a field

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
