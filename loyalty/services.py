from decimal import Decimal
from django.utils import timezone

TIER_INFO = {
    "bronze":   {"label": "Bronze",   "min_spend": Decimal("0"),     "multiplier": Decimal("1.00")},
    "silver":   {"label": "Silver",   "min_spend": Decimal("5000"),  "multiplier": Decimal("1.20")},
    "gold":     {"label": "Gold",     "min_spend": Decimal("20000"), "multiplier": Decimal("1.50")},
    "platinum": {"label": "Platinum", "min_spend": Decimal("50000"), "multiplier": Decimal("2.00")},
}


def compute_tier(total_spent: Decimal) -> str:
    tier = "bronze"
    for name, info in TIER_INFO.items():
        if total_spent >= info["min_spend"]:
            tier = name
    return tier


def award_points_for_order(order):
    """Idempotently award loyalty points when an order is marked paid."""
    from .models import LoyaltyAccount, LoyaltyTransaction
    if order.status != "paid":
        return
    if LoyaltyTransaction.objects.filter(order=order).exists():
        return
    account, _ = LoyaltyAccount.objects.get_or_create(user=order.user)
    base = (order.total / Decimal("100")).to_integral_value(rounding="ROUND_DOWN")
    multiplier = TIER_INFO.get(account.tier, {}).get("multiplier", Decimal("1"))
    points = int(base * multiplier)
    LoyaltyTransaction.objects.create(
        account=account, order=order, points=points,
        reason=f"Purchase on order #{order.id}",
    )
    account.points += points
    account.total_spent += order.total
    account.tier = compute_tier(account.total_spent)
    account.save(update_fields=["points", "total_spent", "tier", "updated_at"])


def validate_discount(discount, user, subtotal):
    """Return (ok, error_message)."""
    if not discount.is_active:
        return False, "This discount is no longer active."
    now = timezone.now()
    if discount.valid_from and discount.valid_from > now:
        return False, "This discount is not yet active."
    if discount.valid_until and discount.valid_until < now:
        return False, "This discount has expired."
    if discount.recipient_id and discount.recipient_id != user.id:
        return False, "This discount was not issued to your account."
    if discount.min_spend and subtotal < discount.min_spend:
        return False, f"Minimum spend of {discount.min_spend} required to use this code."
    if discount.max_uses and discount.used_count >= discount.max_uses:
        return False, "This discount has already been fully redeemed."
    return True, ""