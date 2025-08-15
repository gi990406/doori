from django.conf import settings
from django.db import models
from django.contrib.auth.hashers import check_password

class Order(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "주문접수"
        CONFIRMED = "confirmed", "입금확인"
        DELIVERED = "delivered", "발송완료"
        CANCELLED = "cancelled", "취소"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders"
    )

    # 비회원 정보
    guest_name  = models.CharField(max_length=20, blank=True)
    guest_hp    = models.CharField(max_length=20, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_password = models.CharField(max_length=256, blank=True)  # 해시 저장

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    memo   = models.TextField(blank=True)  # 고객 메모 등
    created_at = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum((i.subtotal() for i in self.items.all()), 0)

    def has_inquiry_only(self):
        return self.items.filter(unit_price__isnull=True).exists()

    def check_guest_password(self, raw_pw):
        return check_password(raw_pw, self.guest_password)

    def __str__(self):
        who = self.user.user_id if self.user_id else self.guest_name or "GUEST"
        return f"Order#{self.pk} by {who}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    part  = models.ForeignKey("parts.Part", null=True, blank=True, on_delete=models.SET_NULL)

    title = models.CharField(max_length=255)          # 스냅샷 제목
    unit_price = models.DecimalField(max_digits=10, decimal_places=0, null=True)  # None → 전화문의
    quantity   = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return 0 if self.unit_price is None else int(self.unit_price) * self.quantity

    def __str__(self):
        return f"{self.title} x{self.quantity}"
