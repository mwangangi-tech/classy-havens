from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from cart.cart import Cart
from catalog.models import ProductVariant
from payments.models import Payment
from payments.services import initialize_paystack_payment
from .forms import ShippingAddressForm
from .models import Order, OrderItem, ShippingAddress


class OutOfStockError(Exception):
    pass


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("catalog:product_list")

    if request.method == "POST":
        form = ShippingAddressForm(request.POST)
        if not form.is_valid():
            return render(request, "orders/checkout.html",
                          {"form": form, "cart": cart})

        try:
            with transaction.atomic():
                address = form.save(commit=False)
                address.user = request.user
                address.save()

                order = Order.objects.create(
                    user=request.user,
                    shipping_address=address,
                    status=Order.Status.PENDING,
                    total=Decimal("0.00"),
                )

                running_total = Decimal("0.00")
                items = list(cart)
                for item in items:
                    variant = item["variant"]
                    qty = item["quantity"]

                    locked = ProductVariant.objects.select_for_update().get(pk=variant.pk)
                    if qty > locked.stock:
                        raise OutOfStockError(locked)

                    unit_price = locked.price
                    OrderItem.objects.create(
                        order=order,
                        variant=locked,
                        quantity=qty,
                        unit_price=unit_price,
                    )
                    running_total += unit_price * qty
                    locked.stock -= qty
                    locked.save()

                order.total = running_total
                order.save()

                Payment.objects.create(
                    order=order,
                    reference=f"CH-{order.id}-pending",
                    amount=order.total,
                    currency=settings.CURRENCY_CODE,
                    status=Payment.Status.INITIATED,
                )
        except OutOfStockError as exc:
            messages.error(request, f"Sorry — not enough stock for {exc}. Please adjust your cart.")
            return redirect("cart:cart_detail")

        # Initialize Paystack outside the DB transaction
        try:
            auth_url, reference = initialize_paystack_payment(order, request.user.email)
        except Exception as exc:
            messages.error(request, f"Payment initialization failed: {exc}")
            return redirect("orders:order_detail", pk=order.pk)

        payment = order.payment
        payment.reference = reference
        payment.save(update_fields=["reference"])

        cart.clear()
        return redirect(auth_url)

    form = ShippingAddressForm(initial={
        "full_name": request.user.get_full_name() or request.user.username,
        "phone": request.user.phone,
    })
    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.user_id != request.user.id and not request.user.is_staff_member:
        messages.error(request, "You do not have access to that order.")
        return redirect("orders:order_list")
    return render(request, "orders/order_detail.html", {"order": order})