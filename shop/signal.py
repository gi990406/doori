from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order

@receiver(pre_save, sender=Order)
def _capture_prev_status(sender, instance: Order, **kwargs):
    if not instance.pk:
        instance._prev_status = None
        return
    try:
        old = Order.objects.get(pk=instance.pk)
        instance._prev_status = old.status
    except Order.DoesNotExist:
        instance._prev_status = None

@receiver(post_save, sender=Order)
def _apply_or_unapply_on_change(sender, instance: Order, created, **kwargs):
    if created:
        return
    prev = getattr(instance, "_prev_status", None)
    now = instance.status

    # prev != confirmed → now == confirmed  ⇒ 차감
    if prev != Order.Status.CONFIRMED and now == Order.Status.CONFIRMED:
        if not instance.stock_applied:
            instance.apply_stock()
        return

    # prev == confirmed → now in {requested, cancelled} ⇒ 복원
    if prev == Order.Status.CONFIRMED and now in (Order.Status.REQUESTED, Order.Status.CANCELLED):
        if instance.stock_applied:
            instance.unapply_stock()
        return
