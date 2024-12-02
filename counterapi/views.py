import random
import string

from datetime import date

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from panelapi.models import (
    Outlet,
    Product,
    OutletCreds, 
    Category,
    Customer,
    Order,
    OrderItem
)

from .serializers import (
    CategorySerializer,
    ProductSerializer,
    CustomerSerializer,
    OrderSerializer
)




# Create your views here.


@swagger_auto_schema(
    method="get",
    responses={
        200: CategorySerializer(many=True),
        500: 'Internal Server Error: Unexpected error'
    },
    operation_description="Fetch all categories available in the system."
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unrestricted access to get categories
def get_all_categories(request):
    try:
        categories = Category.objects.all()  # Fetch all categories
        serializer = CategorySerializer(categories, many=True)  # Serialize the categories
        return Response({
            'error': False,
            'categories': serializer.data  # Only category names will be returned now
        })
    except Exception as e:
        return Response({
            'error': True,
            'detail': str(e)
        }, status=500)











@swagger_auto_schema(
    method='get',
    responses={
        200: ProductSerializer(many=True),
        400: 'Bad Request: Outlet not found',
        500: 'Internal Server Error: Unexpected error'
    },
    operation_description="Fetch products for a specific outlet by outlet_id with associated category names."
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unrestricted access to get products
def get_products_by_outlet(request, outlet_id):
    try:
        # Fetch the outlet by the provided outlet_id
        outlet = Outlet.objects.get(id=outlet_id)
        
        # Get category filter from query params (if provided)
        category_name = request.query_params.get('category', None)

        # Get all products associated with the outlet
        products = Product.objects.filter(outlets=outlet)
        
        # If a category filter is provided, filter products by category
        if category_name:
            category = Category.objects.filter(name__iexact=category_name).first()  # Case-insensitive match
            if category:
                products = products.filter(category=category)
            else:
                return Response({
                    'error': True,
                    'detail': 'Category not found'
                }, status=400)

        # Serialize the products along with the category name
        serializer = ProductSerializer(products, many=True)
        
        return Response({
            'error': False,
            'products': serializer.data  # Return the serialized product data
        })
    
    except Outlet.DoesNotExist:
        return Response({
            'error': True,
            'detail': 'Outlet not found'
        }, status=400)
    
    except Exception as e:
        return Response({
            'error': True,
            'detail': str(e)
        }, status=500)














@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('phone_number', openapi.IN_QUERY, description="Phone number of the customer", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(
            description="Customer found",
            schema=CustomerSerializer
        ),
        400: openapi.Response(
            description="Bad request, missing phone number or invalid outlet ID"
        ),
        404: openapi.Response(
            description="No customer record found"
        ),
        500: openapi.Response(
            description="Internal server error"
        ),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_customer_by_phone_number(request, outlet_id):
    try:
        # Fetch the outlet by the provided outlet_id
        outlet = Outlet.objects.get(id=outlet_id)
        
        # Get phone number from query params
        phone_number = request.query_params.get('phone_number', None)
        
        if not phone_number:
            return Response({
                'error': True,
                'detail': 'Phone number is required'
            }, status=400)
        
        # Get the customer associated with the outlet and the phone number
        customer = Customer.objects.filter(outlet=outlet, phone_number=phone_number).first()
        
        if customer:
            # Serialize the customer data
            serializer = CustomerSerializer(customer)
            return Response({
                'error': False,
                'customer': serializer.data  # Return the serialized customer data
            })
        else:
            return Response({
                'error': True,
                'detail': 'No record found'
            }, status=404)

    except Outlet.DoesNotExist:
        return Response({
            'error': True,
            'detail': 'Outlet not found'
        }, status=400)
    
    except Exception as e:
        return Response({
            'error': True,
            'detail': str(e)
        }, status=500)
















@swagger_auto_schema(
    method='post',
    request_body=CustomerSerializer,
    responses={
        201: openapi.Response(
            description="Customer added successfully",
            schema=CustomerSerializer
        ),
        400: openapi.Response(
            description="Bad request, invalid customer data"
        ),
        500: openapi.Response(
            description="Internal server error"
        ),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_customer(request, outlet_id):
    try:
        # Fetch the outlet by the provided outlet_id
        outlet = Outlet.objects.get(id=outlet_id)
        
        # Extract customer details from the request body
        customer_data = request.data
        
        # Add the outlet to the customer data
        customer_data['outlet'] = outlet.id
        
        # Serialize and validate the customer data
        serializer = CustomerSerializer(data=customer_data)
        
        if serializer.is_valid():
            # Save the customer if valid
            serializer.save()
            return Response({
                'error': False,
                'detail': 'Customer added successfully',
                'customer': serializer.data  # Return the serialized customer data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': True,
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Outlet.DoesNotExist:
        return Response({
            'error': True,
            'detail': 'Outlet not found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': True,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)











# {
#   "customer_phone": "9876543210",
#   "date_of_collection": "2024-12-05",
#   "discount_percentage": 10.0,
#   "total_gst": 50.0,
#   "total_cgst": 25.0,
#   "total_sgst": 25.0,
#   "total_igst": 0.0,
#   "mode_of_payment": "CASH",
#   "order_items": [
#     {
#       "product_id": 1,
#       "quantity": 2
#     },
#     {
#       "product_id": 2,
#       "quantity": 1
#     }
#   ]
# }


@swagger_auto_schema(
    method='post',
    operation_summary="Place an Order",
    operation_description="This endpoint places an order for a specific outlet. It creates the order, links it to the customer, calculates totals, and adds items to the order.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "customer_phone": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Phone number of the customer."
            ),
            "date_of_collection": openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="Date when the order is expected to be collected."
            ),
            "discount_percentage": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format=openapi.FORMAT_FLOAT,
                description="Discount percentage applied to the total amount."
            ),
            "total_gst": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format=openapi.FORMAT_FLOAT,
                description="Total GST amount for the order."
            ),
            "total_cgst": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format=openapi.FORMAT_FLOAT,
                description="Central GST portion of the total GST."
            ),
            "total_sgst": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format=openapi.FORMAT_FLOAT,
                description="State GST portion of the total GST."
            ),
            "total_igst": openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format=openapi.FORMAT_FLOAT,
                description="Integrated GST portion of the total GST."
            ),
            "mode_of_payment": openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=["CASH", "CARD", "UPI", "ONLINE", "OTHER"],
                description="Mode of payment for the order."
            ),
            "order_items": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "product_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="ID of the product."
                        ),
                        "quantity": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Quantity of the product ordered."
                        ),
                    },
                    required=["product_id", "quantity"],
                ),
                description="List of products and their quantities for the order."
            ),
        },
        required=["customer_phone", "order_items"],
        description="Details of the order to be placed."
    ),
    responses={
        201: openapi.Response(
            description="Order placed successfully.",
            examples={
                "application/json": {
                    "error": False,
                    "order_number": "ABC123456789",
                    "message": "Order placed successfully."
                }
            }
        ),
        400: openapi.Response(
            description="Invalid input or missing data.",
            examples={
                "application/json": {
                    "error": True,
                    "detail": "Validation error or missing fields."
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
@api_view(['POST'])
@permission_classes([AllowAny])
def place_order(request, outlet_id):
    try:
        # Validate outlet
        try:
            outlet = Outlet.objects.get(id=outlet_id)
        except Outlet.DoesNotExist:
            return Response({'error': True, 'detail': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)

        # Extract body data
        data = request.data
        customer_phone = data.get('customer_phone')
        date_of_collection = data.get('date_of_collection')
        discount_percentage = data.get('discount_percentage', 0.0)
        total_gst = data.get('total_gst', 0.0)
        total_cgst = data.get('total_cgst', 0.0)
        total_sgst = data.get('total_sgst', 0.0)
        total_igst = data.get('total_igst', 0.0)
        mode_of_payment = data.get('mode_of_payment', 'CASH')
        items = data.get('order_items')

        if not items:
            return Response({'error': True, 'detail': 'Order items are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate customer
        customer = None
        if customer_phone:
            customer, created = Customer.objects.get_or_create(phone_number=customer_phone, defaults={'name': 'Unknown'})

        # Generate order number
        order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

        # Generate invoice number (sequential for outlet)
        last_order = Order.objects.filter(outlet=outlet).order_by('-id').first()
        invoice_number = f"{outlet_id}-{(int(last_order.invoice_number.split('-')[1]) + 1) if last_order else 1}"

        # Calculate totals and create order
        total_amount = 0.0
        with transaction.atomic():
            order = Order.objects.create(
                order_number=order_number,
                outlet=outlet,
                customer=customer,
                date_of_collection=date_of_collection,
                total_amount=0.0,  # Placeholder, will be updated later
                discount_percentage=discount_percentage,
                total_gst=total_gst,
                total_cgst=total_cgst,
                total_sgst=total_sgst,
                total_igst=total_igst,
                mode_of_payment=mode_of_payment,
                invoice_number=invoice_number,
            )

            # Add items to order
            for item in items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 1)

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    return Response({'error': True, 'detail': f'Product with ID {product_id} not found'}, status=status.HTTP_400_BAD_REQUEST)

                total = product.rate_per_unit * quantity
                OrderItem.objects.create(order=order, product=product, quantity=quantity, total=total)
                total_amount += total

            # Update order total amount
            order.total_amount = total_amount - (total_amount * (discount_percentage / 100))
            order.save()

        return Response({
            'error': False,
            'detail': 'Order placed successfully',
            'order_number': order.order_number,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': True, 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
















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
    """
    Retrieve all orders for a specific outlet with optional date and customer filters.
    """
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













@swagger_auto_schema(
    method='post',
    request_body=ProductSerializer,
    responses={201: 'Product added successfully', 400: 'Bad request', 500: 'Internal server error'},
    operation_description="Add a product to a specific outlet using outlet ID."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_product(request, outlet_id):
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













