from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from catalog.models import Product
from orders.models import Order
from .forms import ReviewForm
from .models import Review


@login_required
def submit_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    # OWASP A04 — only buyers can review.
    # Any paid / shipped / delivered order that contained this product counts.
    has_purchased = Order.objects.filter(
        user=request.user,
        status__in=[Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED],
        items__variant__product=product,
    ).exists()

    if not has_purchased:
        messages.error(
            request,
            "You can only review products you've purchased. "
            "Your order must be at least marked as Paid."
        )
        return redirect("catalog:product_detail", slug=product_slug)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.info(request, "You've already reviewed this product.")
        return redirect("catalog:product_detail", slug=product_slug)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.is_approved = False
            review.save()
            messages.success(
                request,
                "Thank you — your review is pending moderation.",
            )
            return redirect("catalog:product_detail", slug=product_slug)
    else:
        form = ReviewForm()

    return render(
        request,
        "reviews/submit_review.html",
        {"form": form, "product": product},
    )