from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Payment
        auditlog.register(Payment)