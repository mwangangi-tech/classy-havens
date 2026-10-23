from decimal import Decimal
from django.conf import settings
from catalog.models import ProductVariant

class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        data = self.session.get(self.SESSION_KEY)
        if data is None:
            data = self.session[self.SESSION_KEY] = {}
        self.cart = data

    def add(self, variant_id, quantity=1, override=False):
        variant_id = str(variant_id)
        if variant_id not in self.cart:
            self.cart[variant_id] = {"quantity": 0}
        if override:
            self.cart[variant_id]["quantity"] = quantity
        else:
            self.cart[variant_id]["quantity"] += quantity
        if self.cart[variant_id]["quantity"] <= 0:
            self.remove(variant_id)
        else:
            self.save()

    def remove(self, variant_id):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[self.SESSION_KEY] = {}
        self.save()

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def __iter__(self):
        variant_ids = self.cart.keys()
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related("product")
        for variant in variants:
            item = self.cart.get(str(variant.id))
            if not item:
                continue
            quantity = item["quantity"]
            yield {
                "variant": variant,
                "product": variant.product,
                "quantity": quantity,
                "unit_price": variant.price,
                "subtotal": variant.price * quantity,
            }

    def total(self):
        return sum(
            (item["subtotal"] for item in self), Decimal("0.00")
        )

    def total_quantity(self):
        return len(self)