import random
import string
import openpyxl

from io import BytesIO

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.db.models import Q


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

from .models import (
    Outlet,
    Product,
    OutletCreds, 
    Category,
    Order,
    OrderItem,
    Customer
)

from .serializers import (
    OutletSerializer,
    ProductSerializer,
    OutletCredsSerializer,
    OrderSerializer,
    OrderItemSerializer,
    CustomerSerializer
)
from users.models import CustomUser






User = get_user_model()







# Create your views here.
@swagger_auto_schema(
    method='post',
    operation_summary="Create a new Outlet",
    manual_parameters=[
        openapi.Parameter(
            name="Authorization",
            in_=openapi.IN_HEADER,
            description="Authorization token",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "owner_name": openapi.Schema(type=openapi.TYPE_STRING, description="Owner's name", example="John Doe"),
            "company_owned": openapi.Schema(type=openapi.TYPE_STRING, description="Company name", example="Tech Corp"),
            "location": openapi.Schema(type=openapi.TYPE_STRING, description="Location", example="Downtown"),
            "address": openapi.Schema(type=openapi.TYPE_STRING, description="Address", example="123 Tech Street"),
            "owner_details": openapi.Schema(type=openapi.TYPE_STRING, description="Owner details", example="Master Admin overseeing multiple outlets"),
        },
        required=["owner_name", "company_owned", "location", "address", "owner_details"]
    ),
    responses={
        status.HTTP_201_CREATED: openapi.Response(
            description="Outlet created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                    "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Outlet created successfully"),
                }
            )
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Response(
            description="Unauthorized - Invalid token",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                    "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Authorization token is missing"),
                }
            )
        ),
        status.HTTP_403_FORBIDDEN: openapi.Response(
            description="Forbidden - Insufficient permissions",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                    "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Only a Master Admin can create outlets"),
                }
            )
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Bad Request - Validation error",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                    "detail": openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        ),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_outlet(request, user_id):
    # Validate token from the Authorization header
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": True, "detail": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Ensure token matches the user ID
            return Response(
                {"error": True, "detail": "Token is not valid. Invalid Authentication Header"},
                status=status.HTTP_403_FORBIDDEN
            )
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": True, "detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the requesting user has the "Master Admin" role
    if requesting_user.role != 'Master Admin':
        return Response(
            {"error": True, "detail": "Only a Master Admin can create outlets"},
            status=status.HTTP_403_FORBIDDEN
        )

    # Process the outlet creation
    try:
        serializer = OutletSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "detail": "Outlet created successfully", "outlet": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"error": True, "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        










@swagger_auto_schema(
    method='get',
    responses={
        200: OutletSerializer(many=True),
        401: 'Unauthorized - Token missing or invalid',
        500: 'Internal Server Error'
    },
    operation_description="Fetch all outlets for the logged-in user. Authorization token required."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_outlets(request):
    try:
        # Manually handle token authentication
        token_key = request.headers.get("Authorization")
        if not token_key:
            return Response({"error": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate the token
        try:
            token = Token.objects.get(key=token_key)
            requesting_user = token.user
        except Token.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Retrieve all outlets
        outlets = Outlet.objects.all()
        serializer = OutletSerializer(outlets, many=True)

        return Response(
            {
                "error": False,
                "detail": "Outlets fetched successfully",
                "outlets": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
        
        
        
        





@swagger_auto_schema(
    method='post',
    request_body=ProductSerializer,
    responses={201: 'Products added successfully', 400: 'Bad request', 500: 'Internal server error'},
    operation_description="Add products from an Excel file."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_products_excel(request, user_id):
    # Validate token from the Authorization header
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": True, "detail": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Ensure token matches the user ID
            return Response(
                {"error": True, "detail": "Token is not valid. Invalid Authentication Header"},
                status=status.HTTP_403_FORBIDDEN
            )
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": True, "detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the requesting user has the "Master Admin" role
    if requesting_user.role != 'Master Admin':
        return Response(
            {"error": True, "detail": "Only a Master Admin can add products"},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        # Retrieve Excel file from the request
        excel_file = request.FILES.get('file')
        if not excel_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Read the Excel file using openpyxl
        wb = openpyxl.load_workbook(BytesIO(excel_file.read()))
        sheet = wb.active
        
        # Retrieve outlet_id from query params
        outlet_id = request.query_params.get('outlet_id', None)
        outlets = []

        if outlet_id:
            # If outlet_id is provided, validate the outlet exists
            try:
                outlet = Outlet.objects.get(id=outlet_id)
                outlets.append(outlet)
            except Outlet.DoesNotExist:
                return Response({"error": "Outlet not found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # If no outlet_id is provided, associate products with all outlets
            outlets = Outlet.objects.all()

        products_added = []
        categories = {category.name.lower(): category for category in Category.objects.all()}  # Dictionary for fast category lookup

        for row in sheet.iter_rows(min_row=2, values_only=True):
            item_name, rate_per_unit, hsn_sac_code, category_name = row  # Extract category name from Excel
            if item_name and rate_per_unit:
                # Check if category is present and matches
                category = categories.get(category_name.strip().lower())  # Convert both to lowercase for comparison
                if not category:
                    continue  # Skip product if category does not match
                
                # Create product for each outlet
                product = Product.objects.create(item_name=item_name, rate_per_unit=rate_per_unit, hsn_sac_code=hsn_sac_code, category=category)
                product.outlets.set(outlets)  # Associate product with the selected outlets
                products_added.append(product)

        return Response(
            {"error": False, "detail": f"{len(products_added)} products added successfully"},
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )












@swagger_auto_schema(
    method='post',
    request_body=ProductSerializer,
    responses={201: 'Product added successfully', 400: 'Bad request', 500: 'Internal server error'},
    operation_description="Add a product to a specific outlet using outlet ID."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_product(request, outlet_id,user_id):
    # Validate token from the Authorization header
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": True, "detail": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Ensure token matches the user ID
            return Response(
                {"error": True, "detail": "Token is not valid. Invalid Authentication Header"},
                status=status.HTTP_403_FORBIDDEN
            )
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": True, "detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # Validate that the outlet_id exists
        try:
            outlet = Outlet.objects.get(id=outlet_id)
        except Outlet.DoesNotExist:
            return Response({"error": "Outlet not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the request data
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            # Save the product
            product = serializer.save()

            # Associate the product with the outlet
            product.outlets.add(outlet)

            return Response(
                {"error": False, "detail": "Product added successfully", "product": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"error": True, "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
















@swagger_auto_schema(
    method='post',
    request_body=OutletCredsSerializer,
    responses={201: 'User and Outlet credentials added successfully', 400: 'Bad request', 500: 'Internal server error'},
    operation_description="Create or update credentials for a user in a specific outlet."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def manage_outlet_creds(request, outlet_id, user_id):
    # Validate token from the Authorization header
    token_key = request.headers.get("Authorization")
    if not token_key:
        return Response({"error": True, "detail": "Authorization token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = Token.objects.get(key=token_key)
        if token.user.id != user_id:  # Ensure token matches the user ID
            return Response(
                {"error": True, "detail": "Token is not valid. Invalid Authentication Header"},
                status=status.HTTP_403_FORBIDDEN
            )
        requesting_user = token.user
    except Token.DoesNotExist:
        return Response({"error": True, "detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the requesting user has the "Master Admin" role
    if requesting_user.role != 'Master Admin':
        return Response(
            {"error": True, "detail": "Only a Master Admin can add credentials"},
            status=status.HTTP_403_FORBIDDEN
        )
    try:
        # Validate if the outlet exists
        try:
            outlet = Outlet.objects.get(id=outlet_id)
        except Outlet.DoesNotExist:
            return Response({"error": "Outlet not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if outlet credentials already exist
        outlet_creds = OutletCreds.objects.filter(
            outlet=outlet, 
            username=request.data.get("username"),
            role=request.data.get("role")  # Filter by role
        ).first()

        if outlet_creds:
            # If credentials exist, update the password
            new_password = request.data.get("password")
            if new_password:
                # Update the password in both CustomUser and OutletCreds model
                user = outlet_creds.user
                user.password = make_password(new_password)  # Hash the new password
                user.save()

                outlet_creds.password = new_password  # Update password in the OutletCreds
                outlet_creds.save()

                return Response(
                    {"error": False, "detail": "Password updated successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response({"error": True, "detail": "Password is required to update credentials."}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # If no credentials found, create a new user and save the credentials
            email = request.data.get("email")
            password = request.data.get("password")
            role = request.data.get("role", "Shop Owner")
            if not email or not password:
                return Response({"error": True, "detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Extract username from email
            username_base = email.split('@')[0]
            username = username_base

            # Ensure the username is unique
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1

            # Create a new user in the CustomUser model
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role=role
            )  # Create user with hashed password

            # Create the outlet credentials
            outlet_creds = OutletCreds.objects.create(
                username=username,
                email=email,
                password=password,
                role=role,
                user=user,
                outlet=outlet
            )

            return Response(
                {"error": False, "detail": "User and Outlet credentials added successfully."},
                status=status.HTTP_201_CREATED
            )

    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )













@swagger_auto_schema(
    method='get',
    responses={200: OutletCredsSerializer, 404: 'Credentials not found'},
    operation_description="Retrieve the credentials for a specific outlet."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_outlet_creds(request, outlet_id):
    try:
        # Retrieve the outlet credentials for the specified outlet ID
        outlet_creds = OutletCreds.objects.filter(outlet_id=outlet_id).first()

        if outlet_creds:
            # If credentials are found, serialize and return them
            serializer = OutletCredsSerializer(outlet_creds)
            return Response(
                {"error": False, "outlet_creds": serializer.data},
                status=status.HTTP_200_OK
            )
        else:
            # If no credentials are found for the outlet, return a 404 response
            return Response(
                {"error": True, "detail": "Credentials not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )











@swagger_auto_schema(
    method='get',
    responses={200: ProductSerializer(many=True), 404: 'No products found for this outlet'},
    operation_description="Retrieve the products for a specific outlet by outlet ID."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_products_for_outlet(request, outlet_id):
    try:
        # Retrieve the outlet object based on the outlet_id from the URL
        outlet = Outlet.objects.get(id=outlet_id)
        
        # Retrieve products associated with the outlet
        products = Product.objects.filter(outlets=outlet)

        if products.exists():
            # If products are found, serialize them and return
            serializer = ProductSerializer(products, many=True)
            return Response(
                {"error": False, "products": serializer.data},
                status=status.HTTP_200_OK
            )
        else:
            # If no products are found for the outlet, return a 404 response
            return Response(
                {"error": True, "detail": "No products found for this outlet"},
                status=status.HTTP_404_NOT_FOUND
            )
    except Outlet.DoesNotExist:
        return Response(
            {"error": True, "detail": "Outlet not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": True, "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


















@swagger_auto_schema(
    method='get',
    operation_summary="Retrieve Orders by Outlet",
    operation_description="Retrieve a list of all orders for a specific outlet with optional filters for date and customer phone number.",
    manual_parameters=[
        openapi.Parameter(
            'start_date',
            openapi.IN_QUERY,
            description="Filter orders starting from this date (YYYY-MM-DD).",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
        ),
        openapi.Parameter(
            'end_date',
            openapi.IN_QUERY,
            description="Filter orders up to this date (YYYY-MM-DD).",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
        ),
        openapi.Parameter(
            'customer_phone',
            openapi.IN_QUERY,
            description="Filter orders by the customer's phone number.",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        200: openapi.Response(
            description="A list of orders for the specified outlet.",
            examples={
                "application/json": {
                    "error": False,
                    "orders": [
                        {
                            "order_number": "ABC12345",
                            "date_of_billing": "2024-12-01",
                            "invoice_number": "INV001",
                            "total_amount": "1000.00",
                            "discount_percentage": "10.00",
                            "total_gst": "180.00",
                            "total_cgst": "90.00",
                            "total_sgst": "90.00",
                            "total_igst": "0.00",
                            "mode_of_payment": "CASH"
                        }
                    ]
                }
            }
        ),
        404: openapi.Response(
            description="No orders found for the given filters or outlet not found.",
            examples={
                "application/json": {
                    "error": True,
                    "detail": "Outlet not found."
                }
            }
        ),
        500: openapi.Response(
            description="Internal server error.",
            examples={
                "application/json": {
                    "error": True,
                    "detail": "An unexpected error occurred."
                }
            }
        ),
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_orders_by_outlet(request, outlet_id):
    try:
        # Validate outlet existence
        outlet = Outlet.objects.get(id=outlet_id)
        
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        customer_phone = request.query_params.get('customer_phone')

        # Build filters
        filters = Q(outlet=outlet)
        if start_date:
            filters &= Q(date_of_billing__gte=start_date)
        if end_date:
            filters &= Q(date_of_billing__lte=end_date)
        if customer_phone:
            try:
                customer = Customer.objects.get(phone_number=customer_phone)
                filters &= Q(customer=customer)
            except Customer.DoesNotExist:
                return Response({
                    "error": True,
                    "detail": "No orders found for the given customer phone number."
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Query orders with applied filters
        orders = Order.objects.filter(filters).order_by('-date_of_billing')

        # Serialize results
        serializer = OrderSerializer(orders, many=True)

        return Response({
            "error": False,
            "orders": serializer.data
        }, status=status.HTTP_200_OK)

    except Outlet.DoesNotExist:
        return Response({
            "error": True,
            "detail": "Outlet not found."
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": True,
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
















@api_view(['GET'])
def get_order_details(request, order_number):
    try:
        # Fetch the order by order_number
        order = Order.objects.prefetch_related('order_items', 'customer').get(order_number=order_number)
        serializer = OrderSerializer(order)
        
        return Response({
            'error': False,
            'detail': 'Order details fetched successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        return Response({
            'error': True,
            'detail': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': True,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)











