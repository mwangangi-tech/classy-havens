import logging

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed

from .models import CustomUser

security_logger = logging.getLogger("security")

ROLE_GROUP_MAP = {
    CustomUser.Roles.STAFF:   "Staff",
    CustomUser.Roles.MANAGER: "Manager",
    CustomUser.Roles.ADMIN:   "Admin",
}


@receiver(post_save, sender=CustomUser)
def assign_role_group(sender, instance, created, **kwargs):
    target = ROLE_GROUP_MAP.get(instance.role)
    all_role_groups = list(ROLE_GROUP_MAP.values())

    # Remove from every role group except the current one.
    stale = instance.groups.filter(name__in=all_role_groups)
    if target:
        stale = stale.exclude(name=target)
    instance.groups.remove(*stale)

    if not target:
        return
    try:
        group = Group.objects.get(name=target)
    except Group.DoesNotExist:
        security_logger.warning(
            "Role group %r does not exist — run `python manage.py sync_roles`.",
            target,
        )
        return
    instance.groups.add(group)


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    security_logger.info(
        "user_logged_in user=%s ip=%s",
        user.username, request.META.get("REMOTE_ADDR"),
    )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request=None, **kwargs):
    security_logger.warning(
        "user_login_failed user=%s ip=%s",
        credentials.get("username"),
        request.META.get("REMOTE_ADDR") if request else "-",
    )