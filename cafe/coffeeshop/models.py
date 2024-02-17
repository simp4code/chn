from django.db import models
import random
from django.utils import timezone

# Create your models here.
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    img = models.ImageField(null=True,blank=True,upload_to='static/images/', default='images/questionmark.jpeg')
    name = models.CharField(max_length=255)
    price = models.FloatField(max_length=100)
    quantity = models.IntegerField(null=True,blank=True)
    
    def __str__(self) -> str:
        return self.file_name
    
class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product.price * self.quantity

class QRCodeData(models.Model):
    cart_items = models.JSONField() 
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    verification_code = models.CharField(max_length=50)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.verification_code

class Orders(models.Model):
    ORDER_STATUS_CHOICES = [
        ('preparing', 'Preparing'),
        ('serving', 'Serving'),
    ]
    
    cart_items = models.JSONField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    verification_code = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='preparing')
    order_number = models.CharField(max_length=10, default=f"ORD-{random.randint(1000, 9999)}")

    def __str__(self):
        return f"{self.verification_code} - {self.status} - {self.order_number}"

class ServedProduct(models.Model):
    product_name = models.CharField(max_length=255)
    served_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.product_name