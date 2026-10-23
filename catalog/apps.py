from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Category, Product, ProductVariant
        for model in (Category, Product, ProductVariant):
            auditlog.register(model)