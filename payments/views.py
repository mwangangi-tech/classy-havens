import hmac
import hashlib
import json
import logging
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from orders.models import Order
from .models import Payment
from .services import verify_paystack_payment

security_logger = logging.getLogger("security")

def _mark_paid(payment, raw):
    if payment.status == Payment.Status.SUCCESS:
        return  # idempotent
    payment.status = Payment.Status.SUCCESS
    payment.paystack_response = raw
    payment.save()
    order = payment.order
    if order.status == Order.Status.PENDING:
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save()
    security_logger.info(
        "payment_success ref=%s order=%s amount=%s",
        payment.reference, order.id, payment.amount,
    )

@login_required
def callback(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")
    if not reference:
        messages.error(request, "Missing payment reference.")
        return redirect("catalog:product_list")

    try:
        payment = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect("catalog:product_list")

    ok, raw = verify_paystack_payment(reference)
    if ok:
        _mark_paid(payment, raw)
        messages.success(request, "Payment successful. Thank you!")
        return redirect("orders:order_detail", pk=payment.order_id)

    payment.status = Payment.Status.FAILED
    payment.paystack_response = raw
    payment.save()
    security_logger.warning("payment_failed ref=%s", reference)
    messages.error(request, "Payment verification failed.")
    return redirect("orders:order_detail", pk=payment.order_id)

@csrf_exempt
@require_POST
def webhook(request):
    """Paystack webhook — signature must be verified (OWASP A08)."""
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        return HttpResponseBadRequest("missing-signature")

    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        request.body,
        hashlib.sha512,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        security_logger.warning("paystack_webhook_bad_signature")
        return HttpResponseBadRequest("bad-signature")

    try:
        event = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("bad-json")

    if event.get("event") == "charge.success":
        ref = event.get("data", {}).get("reference")
        if ref:
            try:
                payment = Payment.objects.get(reference=ref)
                _mark_paid(payment, event)
            except Payment.DoesNotExist:
                security_logger.warning("paystack_webhook_unknown_ref ref=%s", ref)

    return HttpResponse(status=200)