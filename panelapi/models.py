from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now

User = get_user_model()  # Reference to the custom user model


# Create your models here.
class Outlet(models.Model):
    owner_name = models.CharField(max_length=255)
    company_owned = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    address = models.TextField()
    owner_details = models.TextField()

    def __str__(self):
        return f"{self.owner_name} - {self.company_owned}"
    
    


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name




    


class Product(models.Model):
    item_name = models.CharField(max_length=255)
    rate_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    hsn_sac_code = models.CharField(max_length=20, blank=True, null=True)
    outlets = models.ManyToManyField(Outlet, related_name="products")  # Many-to-Many relationship with Outlet
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    def __str__(self):
        return self.item_name
    
    
    




class OutletCreds(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outlet_creds")
    outlet = models.ForeignKey("Outlet", on_delete=models.CASCADE, related_name="credentials")

    def __str__(self):
        return f"{self.username} - {self.user.username} - {self.outlet.owner_name}"






class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)
    state = models.CharField(max_length=100)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='customers')
    address = models.TextField(blank=True, null=True)  # Added address field
    reference = models.TextField(blank=True, null=True)  # Added address field

    def __str__(self):
        return self.name
    
    





class Order(models.Model):
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
        ('ONLINE', 'Online Payment'),
        ('OTHER', 'Other'),
    ]

    order_number = models.CharField(max_length=20, unique=True)
    outlet = models.ForeignKey("Outlet", on_delete=models.CASCADE, related_name="orders")
    customer = models.ForeignKey("Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    date_of_billing = models.DateField(default=now)
    invoice_number = models.CharField(max_length=20, unique=True)
    date_of_collection = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_gst = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_cgst = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    total_sgst = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    total_igst = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    mode_of_payment = models.CharField(max_length=20, choices=PAYMENT_MODES, default='CASH')
    # New field to store the total amount after GST
    total_after_gst = models.DecimalField(max_digits=15, decimal_places=2, default=0.00,blank=True, null=True)
    total_after_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00,blank=True, null=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.outlet.owner_name}"
    
    







class OrderItem(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField(default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"Order {self.order.order_number} - {self.product.item_name}"