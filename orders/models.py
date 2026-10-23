from decimal import Decimal
from django.conf import settings
from django.db import models
from django.urls import reverse
from catalog.models import ProductVariant
from .countries import COUNTRY_CHOICES


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="addresses",
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    street = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(
        max_length=100,
        choices=COUNTRY_CHOICES,
        default="Kenya",
        help_text="Destination country for this order.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} — {self.street}, {self.city}, {self.country}"

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING   = "pending",   "Pending"
        PAID      = "paid",      "Paid"
        SHIPPED   = "shipped",   "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name="orders")
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.user.username}"

    def get_absolute_url(self):
        return reverse("orders:order_detail", args=[self.id])

    def can_review(self, product):
        if self.status != self.Status.DELIVERED:
            return False
        return self.items.filter(variant__product=product).exists()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.variant} × {self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity