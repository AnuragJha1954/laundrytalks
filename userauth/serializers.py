from rest_framework import serializers
from users.models import CustomUser
from datetime import date, timedelta



class CustomUserLoginSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["Master Admin", "Shop Owner"], write_only=True)

    def validate(self, data):
        email = data.get('username')
        password = data.get('password')
        role = data.get('role')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        # Check if the password matches
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        if user.role != role:
            raise serializers.ValidationError(f"User does not have the role '{role}'.")

        data['user'] = user
        return data
