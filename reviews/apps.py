from django.apps import AppConfig

class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Review
        auditlog.register(Review)