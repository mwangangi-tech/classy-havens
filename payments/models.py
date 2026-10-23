from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        SUCCESS   = "success",   "Success"
        FAILED    = "failed",    "Failed"

    order = models.OneToOneField(
        "orders.Order", on_delete=models.PROTECT, related_name="payment",
    )
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="KES")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INITIATED,
    )
    paystack_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.reference} — {self.amount} {self.currency} ({self.status})"