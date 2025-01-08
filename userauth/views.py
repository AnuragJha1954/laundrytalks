import random

from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from .serializers import ( 
    CustomUserLoginSerializer
)

from panelapi.models import (
    Outlet,
    OutletCreds
)

from users.models import CustomUser


# Create your views here.
@swagger_auto_schema(
    method="post",
    request_body=CustomUserLoginSerializer,
    responses={
        status.HTTP_200_OK: "User Logged in successfully",
        status.HTTP_400_BAD_REQUEST: "Invalid credentials",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    try:
        if request.method == "POST":
            serializer = CustomUserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                role = request.data.get("role", "")
                token, _ = Token.objects.get_or_create(user=user)

                # Generate slug from first name and last name
                slug = (user.first_name + user.last_name).lower().replace(" ", "")

                # Common user details
                user_details = {
                    "id": user.id,
                    "username": user.username,
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "is_active": user.is_active,
                    "date_joined": user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    "slug": slug,
                }

                response_data = {
                    "error": False,
                    "detail": "User logged in successfully",
                    "token": token.key,
                    "user_details": user_details,
                }

                # Role-specific logic
                if role == "Master Admin":
                    response_data["role"] = "Master Admin"
                elif role == "Shop Owner":
                    # Fetch outlet details
                    outlet_creds = OutletCreds.objects.filter(user=user).first()
                    if not outlet_creds:
                        return Response(
                            {"error": True, "detail": "No outlet linked with the user."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    outlet = Outlet.objects.filter(id=outlet_creds.outlet_id).first()
                    if not outlet:
                        return Response(
                            {"error": True, "detail": "Outlet not found."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    outlet_details = {
                        "id": outlet.id,
                        "owner_name": outlet.owner_name,
                        "address": outlet.address,
                        "location": outlet.location,
                        "company_owned": outlet.company_owned,
                        "owner_details": outlet.owner_details,
                    }

                    response_data.update({
                        "outlet_details": outlet_details,
                    })

                return Response(response_data, status=status.HTTP_200_OK)

            return Response(
                {"error": True, "detail": "Invalid username, password, or role"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

