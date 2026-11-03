from decimal import Decimal
from django.conf import settings
from django.db import models


class LoyaltyAccount(models.Model):
    class Tier(models.TextChoices):
        BRONZE   = "bronze",   "Bronze"
        SILVER   = "silver",   "Silver"
        GOLD     = "gold",     "Gold"
        PLATINUM = "platinum", "Platinum"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="loyalty",
    )
    points = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.BRONZE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.get_tier_display()} ({self.points} pts)"


class LoyaltyTransaction(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name="transactions")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True)
    points = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.user.username} {'+' if self.points >= 0 else ''}{self.points} pts"


class Discount(models.Model):
    class Type(models.TextChoices):
        PERCENT = "percent", "Percentage"
        FIXED   = "fixed",   "Fixed amount"

    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=10, choices=Type.choices, default=Type.PERCENT)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name="received_discounts",
        help_text="Leave blank for any customer.",
    )
    is_active = models.BooleanField(default=True)
    valid_from  = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True,
        on_delete=models.SET_NULL, related_name="created_discounts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} — {self.value}{'%' if self.discount_type == 'percent' else ' off'}"

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        if self.discount_type == self.Type.PERCENT:
            return (subtotal * self.value / Decimal("100")).quantize(Decimal("0.01"))
        return min(self.value, subtotal)