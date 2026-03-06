from rest_framework import serializers
from panelapi.models import (
    Category,
    Product,
    Customer,
    Order,
    OrderItem,
    Brand,
    Pattern,
    StainType,
    DefectType,
    MaterialType,
    StarchType,
    DetergentType,
    DetergentScentType,
    WashTemperatureType,
    FabricSoftenerType,
    Colour,
    TopUpService,
    OrderItemSpecification,
)




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']  # Return category id and name





class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)  # Make category_name write-only

    class Meta:
        model = Product
        fields = ['id','item_name', 'rate_per_unit', 'hsn_sac_code', 'category_name']  # Include category_name
        ref_name = "CounterAPI_ProductSerializer"

    def create(self, validated_data):
        # Extract category_name from validated data
        category_name = validated_data.pop('category_name')
        
        # Get the category object or raise an error if not found
        category = Category.objects.get(name=category_name)

        # Create the product
        product = Product.objects.create(category=category, **validated_data)

        return product
    
        
        




class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number', 'state', 'gst_number', 'outlet','address','reference']  # Include 'outlet' as a field

    def validate(self, data):
        if not data.get('name'):
            raise serializers.ValidationError("Name is required.")
        if not data.get('phone_number'):
            raise serializers.ValidationError("Phone number is required.")
        if not data.get('state'):
            raise serializers.ValidationError("State is required.")
        return data









class OrderItemSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemSpecification
        fields = [
            'id',
            'brand',
            'pattern',
            'stain_type',
            'defect_type',
            'material_type',
            'starch_type',
            'detergent_type',
            'detergent_scent_type',
            'wash_temperature_type',
            'fabric_softener_type',
            'colour',
            'top_up_service',
            'box',
            'fold',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    specification = OrderItemSpecificationSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'total', 'hanger', 'specification']


class OrderSerializer(serializers.ModelSerializer):
    # now read_only so it’s returned in responses
    order_items = OrderItemSerializer(many=True, read_only=True)

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


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class PatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = "__all__"


class StainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StainType
        fields = "__all__"


class DefectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectType
        fields = "__all__"


class MaterialTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialType
        fields = "__all__"


class StarchTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StarchType
        fields = "__all__"


class DetergentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetergentType
        fields = "__all__"


class DetergentScentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetergentScentType
        fields = "__all__"


class WashTemperatureTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WashTemperatureType
        fields = "__all__"


class FabricSoftenerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FabricSoftenerType
        fields = "__all__"


class ColourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colour
        fields = "__all__"


class TopUpServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopUpService
        fields = "__all__"