from django.conf import settings


def currency(request):
    """Expose the store currency to every template."""
    return {
        "CURRENCY_CODE": settings.CURRENCY_CODE,
        "CURRENCY_SYMBOL": settings.CURRENCY_SYMBOL,
    }