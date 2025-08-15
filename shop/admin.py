from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "user_name", "guest_name", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "guest_name", "guest_hp", "guest_email", "user__user_id")
    inlines = [OrderItemInline]

    def user_name(self, obj):
        # 회원 주문인 경우 회원 이름, 아니면 '-'
        return obj.user.name if obj.user else "-"
    user_name.short_description = "회원명"
