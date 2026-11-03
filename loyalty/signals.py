from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order
from .services import award_points_for_order


@receiver(post_save, sender=Order)
def _award_points(sender, instance, **kwargs):
    if instance.status == Order.Status.PAID and instance.paid_at is not None:
        award_points_for_order(instance)