from django.contrib import admin, messages
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "user_name", "user_hp", "guest_name", "status", "created_at")
    list_filter  = ("status", "stock_applied", "created_at")
    search_fields = ("id", "guest_name", "guest_hp", "guest_email", "user__user_id")
    inlines = [OrderItemInline]
    actions = ["confirm_and_apply_stock", "revert_to_requested_and_restore", "cancel_and_restore"]

    def user_name(self, obj):
        # 회원 주문인 경우 회원 이름, 아니면 '-'
        return obj.user.name if obj.user else "-"
    user_name.short_description = "회원명"

    def user_hp(self, obj):
        # 회원 주문인 경우 회원 이름, 아니면 '-'
        return obj.user.hp if obj.user else "-"
    user_name.short_description = "회원 H.P"

    @admin.action(description="입금확인 + 재고 차감")
    def confirm_and_apply_stock(self, request, queryset):
        done, skipped = 0, 0
        for o in queryset:
            if o.stock_applied and o.status == Order.Status.CONFIRMED:
                skipped += 1
                continue
            o.status = Order.Status.CONFIRMED
            o.save(update_fields=["status"])  # post_save 시그널이 apply_stock 호출
            if not o.stock_applied:
                o.apply_stock()  # 시그널 미로드 대비
            done += 1
        self.message_user(request, f"처리 {done}건, 건너뜀 {skipped}건", level=messages.SUCCESS)

    @admin.action(description="주문접수로 되돌리기 + 재고 복원")
    def revert_to_requested_and_restore(self, request, queryset):
        done, skipped = 0, 0
        for o in queryset:
            if o.stock_applied:  # confirmed에서 내려오는 케이스
                o.unapply_stock()
            o.status = Order.Status.REQUESTED
            o.save(update_fields=["status"])
            done += 1
        self.message_user(request, f"처리 {done}건, 건너뜀 {skipped}건", level=messages.SUCCESS)

    @admin.action(description="주문취소 + 재고 복원")
    def cancel_and_restore(self, request, queryset):
        done, skipped = 0, 0
        for o in queryset:
            if o.stock_applied:
                o.unapply_stock()
            o.status = Order.Status.CANCELLED
            o.save(update_fields=["status"])
            done += 1
        self.message_user(request, f"처리 {done}건, 건너뜀 {skipped}건", level=messages.SUCCESS)
