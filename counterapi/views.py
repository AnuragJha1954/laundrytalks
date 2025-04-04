import random
import string
import qrcode
import base64

from io import BytesIO

from datetime import date, datetime

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.utils.timezone import now


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from num2words import num2words 

from decimal import Decimal, ROUND_HALF_UP

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
        categories = Category.objects.values_list('name', flat=True)  # Fetch only category names as a flat list
        return Response({
            'error': False,
            'categories': list(categories)  # Convert the queryset to a list
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
        
        # Extract customer details from the request body and make it mutable
        customer_data = request.data.copy()  # Make the QueryDict mutable
        
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







def print_bill(order_number):
    try:
        # Fetch the order details
        order = Order.objects.select_related('customer', 'outlet').get(order_number=order_number)
        order_items = OrderItem.objects.filter(order=order).select_related('product')

        if not order_items.exists():
            return Response({'error': True, 'detail': 'No items found in the order'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate order totals
        total_quantity = sum(item.quantity for item in order_items)
        total_discount = Decimal(order.total_amount) * (Decimal(order.discount_percentage) / Decimal(100)) if order.discount_percentage > 0 else Decimal(0)
        net_amount = Decimal(order.total_amount) - total_discount  # Net amount already includes GST

        sgst = Decimal(order.total_sgst)
        cgst = Decimal(order.total_cgst)
        igst = Decimal(order.total_igst)

        # Calculate round-off and grand amount
        calculated_total = net_amount  # Since GST is already included, total remains the same
        rounded_total = calculated_total.quantize(Decimal('1'), rounding="ROUND_HALF_UP")  # Round to the nearest integer
        round_off = rounded_total - calculated_total  # Difference between rounded total and actual total
        grand_amount = rounded_total  # Grand total is the rounded value

        # Convert grand total into words
        total_in_words = num2words(grand_amount, to='currency', currency='INR', lang='en_IN').replace("zero paise", "").replace("-", " ").replace(",", "").title()

        # UPI payment details
        upi_id = "vyapar.171035825947@hdfcbank"
        name = "Laundry Talks"

        # Generate UPI URL and QR Code
        upi_url = f"upi://pay?pa={upi_id}&pn={name}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(upi_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Save QR code image to BytesIO buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer)
        qr_buffer.seek(0)

        # Convert QR code image to base64
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

        # Build context for the template
        context = {
            "customer_name": order.customer.name if order.customer else "Walk-in Customer",
            "billing_date": order.date_of_billing.strftime('%Y-%m-%d'),
            "customer_address": order.customer.address if order.customer else "Not Provided",
            "invoice_number": order.invoice_number,
            "customer_phone": order.customer.phone_number if order.customer else "Not Provided",
            "reference": order.customer.reference if order.customer and hasattr(order.customer, "reference") else "N/A",
            "gst_number": order.customer.gst_number if order.customer else "Not Provided",
            "collection_date": order.date_of_collection.strftime('%Y-%m-%d') if order.date_of_collection else "Not Provided",
            "items": [
                {
                    "description": item.product.item_name,
                    "hanger": item.hanger,  # Include the hanger value
                    "hsn_code": item.product.hsn_sac_code if hasattr(item.product, "hsn_sac_code") else " ",
                    "quantity": item.quantity,
                    "rate": round(item.product.rate_per_unit,2 ),  # Extract GST from rate
                    "total": round(item.total , 2),  # Extract GST from total
                } for item in order_items
            ],
            "total_quantity": total_quantity,
            "total_amount": "{:.2f}".format(order.total_amount),
            "discount_percentage": "{:.2f}".format(order.discount_percentage) if order.discount_percentage > 0 else "0.00",
            "discount": "{:.2f}".format(total_discount),
            "net_amount": "{:.2f}".format(net_amount),  # Now it's the base price before GST
            "sgst": "{:.2f}".format(sgst) if sgst > 0 else None,
            "cgst": "{:.2f}".format(cgst) if cgst > 0 else None,
            "igst": "{:.2f}".format(igst) if igst > 0 else None,
            "round_off": "{:.2f}".format(round_off),
            "grand_amount": "{:.2f}".format(grand_amount),
            "total_in_words": total_in_words + " Only.",
            "qr_code": qr_base64
        }

        # Render the template
        return render(None, "bill.html", context)

    except Order.DoesNotExist:
        return Response({'error': True, 'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': True, 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# def print_bill(order_number):
#     try:
#         # Fetch the order details
#         order = Order.objects.select_related('customer', 'outlet').get(order_number=order_number)
#         order_items = OrderItem.objects.filter(order=order).select_related('product')

#         if not order_items.exists():
#             return Response({'error': True, 'detail': 'No items found in the order'}, status=status.HTTP_404_NOT_FOUND)

#         # # Get HSN code from the first product
#         # first_product = order_items.first().product
#         # hsn_code = first_product.hsn_sac_code if hasattr(first_product, 'hsn_sac_code') else "N/A"

#         # Calculate order totals
#         total_quantity = sum(item.quantity for item in order_items)
#         total_discount = Decimal(order.total_amount) * (Decimal(order.discount_percentage) / Decimal(100)) if order.discount_percentage > 0 else Decimal(0)
#         net_amount = Decimal(order.total_amount) - total_discount
#         sgst = Decimal(order.total_sgst)
#         cgst = Decimal(order.total_cgst)
#         igst = Decimal(order.total_igst)

#         # Calculate round-off and grand amount
#         calculated_total = net_amount + sgst + cgst + igst
#         rounded_total = calculated_total.quantize(Decimal('1'), rounding="ROUND_HALF_UP")  # Round to the nearest integer
#         round_off = rounded_total - calculated_total  # Difference between rounded total and actual total
#         grand_amount = rounded_total  # Grand total is the rounded value

#         # Convert grand total into words
#         total_in_words = num2words(grand_amount, to='currency', currency='INR', lang='en_IN').replace("zero paise", "").replace("-", " ").replace(",", "").title()

#         # UPI payment details
#         upi_id = "vyapar.171035825947@hdfcbank"
#         name = "Laundry Talks"

#         # Generate UPI URL and QR Code
#         upi_url = f"upi://pay?pa={upi_id}&pn={name}"
#         qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
#         qr.add_data(upi_url)
#         qr.make(fit=True)
#         qr_img = qr.make_image(fill_color="black", back_color="white")

#         # Save QR code image to BytesIO buffer
#         qr_buffer = BytesIO()
#         qr_img.save(qr_buffer)
#         qr_buffer.seek(0)

#         # Convert QR code image to base64
#         qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

#         # Build context for the template
#         context = {
#             "customer_name": order.customer.name if order.customer else "Walk-in Customer",
#             "billing_date": order.date_of_billing.strftime('%Y-%m-%d'),
#             "customer_address": order.customer.address if order.customer else "Not Provided",
#             "invoice_number": order.invoice_number,
#             "customer_phone": order.customer.phone_number if order.customer else "Not Provided",
#             "reference": order.customer.reference if order.customer and hasattr(order.customer, "reference") else "N/A",
#             "gst_number": order.customer.gst_number if order.customer else "Not Provided",
#             "collection_date": order.date_of_collection.strftime('%Y-%m-%d') if order.date_of_collection else "Not Provided",
#             "items": [
#                 {
#                     "description": item.product.item_name,
#                     "hanger": item.hanger,  # Include the hanger value
#                     "hsn_code": item.product.hsn_sac_code if hasattr(item.product, "hsn_sac_code") else " ",
#                     "quantity": item.quantity,
#                     "rate": round(item.product.rate_per_unit, 2),
#                     "total": round(item.total, 2),
#                 } for item in order_items
#             ],
#             "total_quantity": total_quantity,
#             "total_amount": "{:.2f}".format(order.total_amount),
#             "discount_percentage": "{:.2f}".format(order.discount_percentage) if order.discount_percentage > 0 else "0.00",
#             "discount": "{:.2f}".format(total_discount),
#             "net_amount": "{:.2f}".format(net_amount),
#             "sgst": "{:.2f}".format(sgst) if sgst > 0 else None,
#             "cgst": "{:.2f}".format(cgst) if cgst > 0 else None,
#             "igst": "{:.2f}".format(igst) if igst > 0 else None,
#             "round_off": "{:.2f}".format(round_off),
#             "grand_amount": "{:.2f}".format(grand_amount),
#             "total_in_words": total_in_words + " Only.",
#             "qr_code": qr_base64
#         }

#         # Render the template
#         return render(None, "bill.html", context)

#     except Order.DoesNotExist:
#         return Response({'error': True, 'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({'error': True, 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        discount_percentage = Decimal(data.get('discount_percentage', 0.0)).quantize(Decimal('0.00'))
        mode_of_payment = data.get('mode_of_payment', 'CASH')
        items = data.get('order_items')

        if not items:
            return Response({'error': True, 'detail': 'Order items are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse and format date_of_collection
        if date_of_collection:
            try:
                date_of_collection = datetime.fromisoformat(date_of_collection).strftime('%Y-%m-%d')
            except ValueError:
                return Response({'error': True, 'detail': 'Invalid date format. Use ISO 8601 format.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate customer
        customer = None
        if customer_phone:
            customer, created = Customer.objects.get_or_create(
                phone_number=customer_phone, defaults={'name': 'Unknown'}
            )

        # Generate order number
        order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

        # Generate invoice number in the format: outlet_idLTmmyysequential_number
        current_date = now()
        month_year = current_date.strftime('%m%y')
        last_order = Order.objects.filter(outlet=outlet, invoice_number__startswith=f"{outlet_id}LT{month_year}").order_by('-id').first()

        if last_order:
            # Extract the sequential number from the end of the invoice number
            sequential_part = last_order.invoice_number[len(f"{outlet_id}LT{month_year}"):]
            if sequential_part.isdigit():
                last_invoice_number = int(sequential_part)
            else:
                return Response({'error': True, 'detail': 'Invalid format for last invoice number'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            next_invoice_number = last_invoice_number + 1
        else:
            next_invoice_number = 1

        # Construct the new invoice number
        invoice_number = f"{outlet_id}LT{month_year}{next_invoice_number}"

        # Calculate totals and create order
        total_amount = Decimal('0.00')  # Use Decimal for accurate monetary calculation
        with transaction.atomic():
            order = Order.objects.create(
                order_number=order_number,
                outlet=outlet,
                customer=customer,
                date_of_collection=date_of_collection,
                total_amount=total_amount,  # Placeholder, will be updated later
                discount_percentage=discount_percentage,
                mode_of_payment=mode_of_payment,
                invoice_number=invoice_number,
            )

            # Add items to order and calculate total
            for item in items:
                product_id = item.get('product_id')
                quantity = Decimal(item.get('quantity', 1)).quantize(Decimal('0.00'))
                hanger = item.get('hanger', False)  # Extract hanger value

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    return Response({'error': True, 'detail': f'Product with ID {product_id} not found'}, status=status.HTTP_400_BAD_REQUEST)

                total = (Decimal(product.rate_per_unit) * quantity).quantize(Decimal('0.00'))
                OrderItem.objects.create(order=order, product=product, quantity=quantity, total=total, hanger=hanger)
                total_amount += total

            # Calculate total after discount
            total_after_discount = total_amount - (total_amount * (discount_percentage / Decimal('100')))

            # Determine GST type
            customer_state = customer.state.lower() if customer and customer.state else ""
            is_uttar_pradesh = (customer_state == "uttar pradesh")

            
            # Extract GST from the already included price
            if is_uttar_pradesh:

                base_price = total_after_discount / Decimal('1.18')  # Removing 18% GST
                cgst = base_price * (Decimal('9') / Decimal('100'))
                sgst = base_price * (Decimal('9') / Decimal('100'))

            else:

                base_price = total_after_discount / Decimal('1.18')  # Removing 18% GST
                cgst = Decimal('0.00')
                sgst = Decimal('0.00')
                igst = base_price * (Decimal('18') / Decimal('100'))

            # Final total remains the same (already inclusive of GST)
            total_gst = (cgst + sgst + igst).quantize(Decimal('0.00'))
            total_after_gst = total_after_discount  # No additional GST is added
            
            # Update order fields
            order.total_amount = total_amount.quantize(Decimal('0.00'))  # Total before discount
            order.total_after_discount = total_after_discount.quantize(Decimal('0.00'))
            order.total_gst = total_gst
            order.total_cgst = cgst.quantize(Decimal('0.00'))
            order.total_sgst = sgst.quantize(Decimal('0.00'))
            order.total_igst = igst.quantize(Decimal('0.00'))
            order.total_after_gst = total_after_gst  # Same as total_after_discount (since GST is included)
            order.save()

        response = print_bill(order.order_number)  # Assuming print_bill is defined elsewhere
        return response

    except Exception as e:
        return Response({'error': True, 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# def place_order(request, outlet_id):
#     try:
#         # Validate outlet
#         try:
#             outlet = Outlet.objects.get(id=outlet_id)
#         except Outlet.DoesNotExist:
#             return Response({'error': True, 'detail': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)

#         # Extract body data
#         data = request.data
#         customer_phone = data.get('customer_phone')
#         date_of_collection = data.get('date_of_collection')
#         discount_percentage = Decimal(data.get('discount_percentage', 0.0)).quantize(Decimal('0.00'))
#         mode_of_payment = data.get('mode_of_payment', 'CASH')
#         items = data.get('order_items')

#         if not items:
#             return Response({'error': True, 'detail': 'Order items are required'}, status=status.HTTP_400_BAD_REQUEST)

#         # Parse and format date_of_collection
#         if date_of_collection:
#             try:
#                 date_of_collection = datetime.fromisoformat(date_of_collection).strftime('%Y-%m-%d')
#             except ValueError:
#                 return Response({'error': True, 'detail': 'Invalid date format. Use ISO 8601 format.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Validate customer
#         customer = None
#         if customer_phone:
#             customer, created = Customer.objects.get_or_create(
#                 phone_number=customer_phone, defaults={'name': 'Unknown'}
#             )

#         # Generate order number
#         order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

#         # Generate invoice number in the format: outlet_idLTmmyysequential_number
#         current_date = now()
#         month_year = current_date.strftime('%m%y')
#         last_order = Order.objects.filter(outlet=outlet, invoice_number__startswith=f"{outlet_id}LT{month_year}").order_by('-id').first()

#         if last_order:
#             # Extract the sequential number from the end of the invoice number
#             sequential_part = last_order.invoice_number[len(f"{outlet_id}LT{month_year}"):]
#             if sequential_part.isdigit():
#                 last_invoice_number = int(sequential_part)
#             else:
#                 return Response({'error': True, 'detail': 'Invalid format for last invoice number'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#             next_invoice_number = last_invoice_number + 1
#         else:
#             next_invoice_number = 1

#         # Construct the new invoice number
#         invoice_number = f"{outlet_id}LT{month_year}{next_invoice_number}"

#         # Calculate totals and create order
#         total_amount = Decimal('0.00')  # Use Decimal for accurate monetary calculation
#         with transaction.atomic():
#             order = Order.objects.create(
#                 order_number=order_number,
#                 outlet=outlet,
#                 customer=customer,
#                 date_of_collection=date_of_collection,
#                 total_amount=total_amount,  # Placeholder, will be updated later
#                 discount_percentage=discount_percentage,
#                 mode_of_payment=mode_of_payment,
#                 invoice_number=invoice_number,
#             )

#             # Add items to order and calculate total
#             for item in items:
#                 product_id = item.get('product_id')
#                 quantity = Decimal(item.get('quantity', 1)).quantize(Decimal('0.00'))
#                 hanger = item.get('hanger', False)  # Extract hanger value

#                 try:
#                     product = Product.objects.get(id=product_id)
#                 except Product.DoesNotExist:
#                     return Response({'error': True, 'detail': f'Product with ID {product_id} not found'}, status=status.HTTP_400_BAD_REQUEST)

#                 total = (Decimal(product.rate_per_unit) * quantity).quantize(Decimal('0.00'))
#                 OrderItem.objects.create(order=order, product=product, quantity=quantity, total=total, hanger=hanger)
#                 total_amount += total

#             # Calculate total after discount
#             total_after_discount = total_amount - (total_amount * (discount_percentage / Decimal('100')))

#             # Determine GST type
#             customer_state = customer.state.lower() if customer and customer.state else ""
#             is_uttar_pradesh = (customer_state == "uttar pradesh")
#             print(is_uttar_pradesh)
            
#             if is_uttar_pradesh:
#                 print("in state")
#                 cgst = total_after_discount * (Decimal('9') / Decimal('100'))
#                 sgst = total_after_discount * (Decimal('9') / Decimal('100'))
#                 igst = Decimal('0.00')
#             else:
#                 print("out state")
                
#                 cgst = Decimal('0.00')
#                 sgst = Decimal('0.00')
#                 igst = total_after_discount * (Decimal('18') / Decimal('100'))

#             # Final total with GST
#             total_gst = (cgst + sgst + igst).quantize(Decimal('0.00'))
#             total_after_gst = (total_after_discount + total_gst).quantize(Decimal('0.00'))

#             print(cgst.quantize(Decimal('0.00')))
#             print(sgst.quantize(Decimal('0.00')))
#             print(igst.quantize(Decimal('0.00')))
            
#             # Update order fields
#             order.total_amount = total_amount.quantize(Decimal('0.00'))  # Total before discount
#             order.total_after_discount = total_after_discount.quantize(Decimal('0.00'))
#             order.total_gst = total_gst
#             order.total_cgst = cgst.quantize(Decimal('0.00'))
#             order.total_sgst = sgst.quantize(Decimal('0.00'))
#             order.total_igst = igst.quantize(Decimal('0.00'))
#             order.total_after_gst = total_after_gst
#             order.save()

#         response = print_bill(order.order_number)  # Assuming print_bill is defined elsewhere
#         return response

#     except Exception as e:
#         return Response({'error': True, 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)















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













# def invoice_view(request):
#     # Context data to pass to the template
#     context = {
#         "customer_name": "John Doe",
#         "billing_date": "2024-12-06",
#         "customer_address": "123, Sample Street, Sample City",
#         "invoice_number": "INV-00123",
#         "customer_phone": "9876543210",
#         "reference": "REF-2024",
#         "gst_number": "09ABCDE1234Z5F1",
#         "collection_date": "2024-12-05",
#         "items": [
#             {"description": "Item 1", "hsn_code": "1234", "quantity": 2, "rate": 100, "total": 200},
#             {"description": "Item 2", "hsn_code": "5678", "quantity": 1, "rate": 500, "total": 500},

#         ],
#         "total_quantity": 3,
#         "total_amount": 700,
#         "discount_percentage": 5,
#         "discount": 35,
#         "net_amount": 665,
#         "sgst": 59.85,
#         "cgst": 59.85,
#         "round_off": 0.3,
#         "grand_amount": 785,
#         "total_in_words": "Seven Hundred Eighty-Five Rupees Only",
#     }
#     return render(request, "bill.html", context)
