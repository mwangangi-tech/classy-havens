from django.core.management.base import BaseCommand, CommandError
from accounts.models import CustomUser


class Command(BaseCommand):
    help = "Promote a user to a role: customer | staff | manager | admin"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "role",
            choices=[r.value for r in CustomUser.Roles],
        )

    def handle(self, *args, **opts):
        try:
            user = CustomUser.objects.get(username=opts["username"])
        except CustomUser.DoesNotExist:
            raise CommandError(f"No user named {opts['username']!r}")

        user.role = opts["role"]
        # superusers should also be is_staff=True for admin access
        if opts["role"] == CustomUser.Roles.ADMIN:
            user.is_staff = True
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"{user.username} → role={user.role} is_staff={user.is_staff} is_superuser={user.is_superuser}"
        ))