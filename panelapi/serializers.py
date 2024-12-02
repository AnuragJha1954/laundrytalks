from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import (
    Outlet,
    Product,
    OutletCreds
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
        fields = ['item_name', 'rate_per_unit', 'hsn_sac_code', 'category']
        ref_name = "PanelAPI_ProductSerializer"

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
        fields = ['username', 'password', 'user', 'outlet']

    def validate(self, data):
        # Ensure the password meets the criteria
        if len(data['password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return data

