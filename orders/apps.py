from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Order, OrderItem
        for model in (Order, OrderItem):
            auditlog.register(model)