from django.contrib import admin
from .models import LoyaltyAccount, LoyaltyTransaction, Discount


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "tier", "points", "total_spent", "updated_at")
    list_filter = ("tier",)
    search_fields = ("user__username", "user__email")


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "points", "order", "reason", "created_at")
    list_filter = ("created_at",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "recipient", "used_count", "max_uses", "is_active")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code", "recipient__username")