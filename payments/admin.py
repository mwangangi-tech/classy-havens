from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "order", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "order__id", "order__user__username")
    readonly_fields = ("paystack_response",)