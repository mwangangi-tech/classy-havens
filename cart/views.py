from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.views.decorators.http import require_POST

from catalog.models import ProductVariant
from .cart import Cart

def cart_detail(request):
    return render(request, "cart/cart_detail.html", {"cart": Cart(request)})

@require_POST
def cart_add(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    quantity = int(request.POST.get("quantity", 1))
    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect("cart:cart_detail")
    if quantity > variant.stock:
        messages.error(request, f"Only {variant.stock} left in stock.")
        return redirect("cart:cart_detail")
    cart.add(variant_id=variant.id, quantity=quantity)
    messages.success(request, f"Added {variant.product.name} to cart.")
    return redirect("cart:cart_detail")

@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    quantity = int(request.POST.get("quantity", 0))
    if quantity > variant.stock:
        messages.error(request, f"Only {variant.stock} left in stock.")
        return redirect("cart:cart_detail")
    cart.add(variant_id=variant.id, quantity=quantity, override=True)
    messages.success(request, "Cart updated.")
    return redirect("cart:cart_detail")

@require_POST
def cart_remove(request, variant_id):
    Cart(request).remove(variant_id)
    messages.info(request, "Item removed from cart.")
    return redirect("cart:cart_detail")