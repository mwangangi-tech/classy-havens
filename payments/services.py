import uuid
import requests
from django.conf import settings


def initialize_paystack_payment(order, email):
    """
    Initialise a Paystack transaction in the configured currency.

    Kenyan merchants must have a KES-enabled Paystack account; otherwise
    Paystack will reject the request with 'Currency not supported'.
    """
    reference = f"CH-{order.id}-{uuid.uuid4().hex[:10]}"
    payload = {
        "email": email,
        "amount": int(order.total * 100),         # subunits (KES cents)
        "currency": settings.CURRENCY_CODE,       # "KES"
        "reference": reference,
        "callback_url": settings.PAYSTACK_CALLBACK_URL,
        "metadata": {"order_id": order.id},
    }
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    resp = requests.post(
        f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
        json=payload, headers=headers, timeout=15,
    )
    data = resp.json()
    if not data.get("status"):
        raise RuntimeError(data.get("message", "Paystack init failed"))
    return data["data"]["authorization_url"], reference


def verify_paystack_payment(reference):
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    resp = requests.get(
        f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=headers, timeout=15,
    )
    data = resp.json()
    ok = bool(data.get("status")) and data.get("data", {}).get("status") == "success"
    return ok, data