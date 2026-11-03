from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

ROLE_PERMISSIONS = {
    "Staff": [
        "view_product", "change_product",
        "view_productvariant",
        "view_order", "change_order",
        "view_payment",
        "view_review",
        "view_contactmessage", "change_contactmessage",
        "view_customuser", "view_loyaltyaccount",
    ],
    "Manager": [
        "add_product", "change_product", "delete_product",
        "view_productvariant", "add_productvariant",
        "change_productvariant", "delete_productvariant",
        "view_category", "add_category", "change_category", "delete_category",
        "view_order", "change_order",
        "view_orderitem",
        "view_payment",
        "view_review", "change_review", "delete_review",
        "view_staffdocument", "add_staffdocument",
        "view_discount", "add_discount", "change_discount",
        "view_contactmessage", "change_contactmessage",
        "view_customuser", "view_loyaltyaccount",
    ],
    "Admin": [
        "view_product", "add_product", "change_product", "delete_product",
        "view_productvariant", "add_productvariant",
        "change_productvariant", "delete_productvariant",
        "view_category", "add_category", "change_category", "delete_category",
        "view_order", "change_order", "delete_order",
        "view_orderitem",
        "view_payment", "change_payment",
        "view_review", "change_review", "delete_review",
        # Staff management (admin only)
        "view_customuser", "add_customuser", "change_customuser",
        "view_staffdocument", "add_staffdocument",
        "change_staffdocument", "delete_staffdocument",
        "view_loyaltyaccount", "change_loyaltyaccount",
        "view_loyaltytransaction",
        "view_discount", "add_discount", "change_discount", "delete_discount",
        "view_contactmessage", "change_contactmessage", "delete_contactmessage",
    ],
}


class Command(BaseCommand):
    help = "Create / update the Staff, Manager, Admin groups with their permissions."

    def handle(self, *args, **options):
        for role_name, codenames in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=role_name)
            perms = Permission.objects.filter(codename__in=codenames)
            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(
                f"Group '{role_name}' {'created' if created else 'updated'} "
                f"with {perms.count()} permissions."
            ))