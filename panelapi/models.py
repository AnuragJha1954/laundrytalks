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
    ROLE_CHOICES = [
        ('Counter Operator', 'Counter Operator'),
        ('Shop Owner', 'Shop Owner'),
    ]
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254,blank=True, null=True)  # Added email field
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Shop Owner')  # Role field added
    password = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outlet_creds")
    outlet = models.ForeignKey("Outlet", on_delete=models.CASCADE, related_name="credentials")

    def __str__(self):
        return f"{self.username} - {self.role} - {self.outlet.owner_name}"






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
    hanger = models.BooleanField(default=False)  # New field
    # NEW: link to specification
    specification = models.ForeignKey(
        "OrderItemSpecification",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )    

    def __str__(self):
        return f"Order {self.order.order_number} - {self.product.item_name}"
    
    
    
    
    # ==============================
# Master / Type Models (New)
# ==============================

class Brand(models.Model):
    """Garment / item brand name."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Pattern(models.Model):
    """Pattern types e.g., checks, stripes, plain."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class StainType(models.Model):
    """Types of stains e.g., oil, ink, mud."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class DefectType(models.Model):
    """Types of defects e.g., tear, missing button."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class MaterialType(models.Model):
    """Fabric / material types e.g., cotton, silk, wool."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class StarchType(models.Model):
    """Starch levels / types e.g., no starch, light, medium, heavy."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class DetergentType(models.Model):
    """Detergent categories e.g., regular, premium, hypoallergenic."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class DetergentScentType(models.Model):
    """Detergent fragrance options e.g., lavender, lemon, no fragrance."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class WashTemperatureType(models.Model):
    """Wash temperature presets e.g., cold, warm, hot, 30°C, 40°C."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class FabricSoftenerType(models.Model):
    """Fabric softener options e.g., normal, premium, no softener."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
    
class Colour(models.Model):
    """Colour options for garments e.g., white, black, navy blue, pastel."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    
class TopUpService(models.Model):
    """Extra value-added services like express delivery, steam press, etc."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name



# ==============================
# Order Item Specification
# ==============================

class OrderItemSpecification(models.Model):
    """Holds detailed specs for a particular order item."""
    brand = models.ForeignKey("Brand", on_delete=models.SET_NULL, null=True, blank=True)
    pattern = models.ForeignKey("Pattern", on_delete=models.SET_NULL, null=True, blank=True)
    stain_type = models.ForeignKey("StainType", on_delete=models.SET_NULL, null=True, blank=True)
    defect_type = models.ForeignKey("DefectType", on_delete=models.SET_NULL, null=True, blank=True)
    material_type = models.ForeignKey("MaterialType", on_delete=models.SET_NULL, null=True, blank=True)
    starch_type = models.ForeignKey("StarchType", on_delete=models.SET_NULL, null=True, blank=True)
    detergent_type = models.ForeignKey("DetergentType", on_delete=models.SET_NULL, null=True, blank=True)
    detergent_scent_type = models.ForeignKey("DetergentScentType", on_delete=models.SET_NULL, null=True, blank=True)
    wash_temperature_type = models.ForeignKey("WashTemperatureType", on_delete=models.SET_NULL, null=True, blank=True)
    fabric_softener_type = models.ForeignKey("FabricSoftenerType", on_delete=models.SET_NULL, null=True, blank=True)
    colour = models.ForeignKey("Colour", on_delete=models.SET_NULL, null=True, blank=True)
    top_up_service = models.ForeignKey("TopUpService", on_delete=models.SET_NULL, null=True, blank=True)

    box = models.BooleanField(default=False)
    fold = models.BooleanField(default=False)

    def __str__(self):
        return f"Specification #{self.id}"


