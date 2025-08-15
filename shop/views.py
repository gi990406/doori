from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .cart import Cart
from parts.models import Part
from django.views.decorators.http import require_http_methods
from .models import Order, OrderItem
from django.contrib.auth.hashers import make_password

def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/cart.html", {"cart": cart})

@require_POST
def cart_add(request, part_id):
    get_object_or_404(Part, id=part_id)  # 존재 확인
    qty = int(request.POST.get("qty", 1))
    Cart(request).add(part_id, qty=qty, replace=False)
    messages.success(request, "장바구니에 담았습니다.")
    return redirect("shop:cart_detail")

@require_POST
def cart_update(request, part_id):
    get_object_or_404(Part, id=part_id)
    qty = int(request.POST.get("qty", 1))
    Cart(request).add(part_id, qty=qty, replace=True)
    messages.success(request, "수량을 변경했습니다.")
    return redirect("shop:cart_detail")

@require_POST
def cart_remove(request, part_id):
    Cart(request).remove(part_id)
    messages.success(request, "상품을 삭제했습니다.")
    return redirect("shop:cart_detail")

@require_http_methods(["GET", "POST"])
def order_form(request):
    cart = Cart(request)

    # 장바구니 검사
    empty = True
    has_inquiry = False
    has_stock_issue = False
    items_snapshot = []
    for it in cart:
        empty = False
        has_inquiry |= (it["price"] is None)
        has_stock_issue |= (not it["stock_ok"])
        items_snapshot.append(it)

    if empty:
        messages.warning(request, "장바구니가 비어 있습니다.")
        return redirect("shop:cart_detail")
    if has_inquiry or has_stock_issue:
        messages.error(request, "전화문의 상품 또는 재고 이슈가 있어 주문할 수 없습니다.")
        return redirect("shop:cart_detail")

    if request.method == "POST":
        # 공통 주문 생성
        order = Order()

        if request.user.is_authenticated:
            # 회원 주문
            order.user = request.user
            order.memo = request.POST.get("memo", "")
        else:
            # 비회원 주문
            order.guest_name  = request.POST.get("name", "").strip()
            order.guest_hp    = request.POST.get("hp", "").strip()
            order.guest_email = request.POST.get("email", "").strip()
            raw_pw = request.POST.get("password", "").strip()
            # 간단 검증
            if not (order.guest_name and order.guest_hp and order.guest_email and raw_pw):
                messages.error(request, "비회원 주문의 필수 정보를 모두 입력해주세요.")
                return redirect("shop:order_form")
            order.guest_password = make_password(raw_pw)
            order.memo = request.POST.get("memo", "")

        order.save()

        # 아이템 스냅샷
        for it in items_snapshot:
            p = it["product"]  # Part
            OrderItem.objects.create(
                order=order,
                part=p,
                title=p.title,
                unit_price=it["price"],   # None이면 전화문의가 아니라 여기선 이미 막혔음
                quantity=it["qty"],
            )

        # 장바구니 비우기
        cart.clear()

        return redirect("shop:complete", order_id=order.id)

    # GET: 폼 표시 (회원/비회원 분기)
    ctx = {
        "cart": cart,
        "is_member": request.user.is_authenticated,
    }
    if request.user.is_authenticated:
        # 회원 기본값 (필요시 사용자 모델 필드명에 맞춰 출력)
        ctx.update({
            "default_name": getattr(request.user, "name", ""),
            "default_hp":   getattr(request.user, "hp", ""),
            "default_email":getattr(request.user, "email", ""),
        })
    return render(request, "orders/order_form.html", ctx)

def order_complete(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    total_amount = sum((item.subtotal() for item in order.items.all()), 0)
    return render(request, "orders/order_complete.html", {
        "order": order,
        "total_amount": total_amount,
    })

@require_http_methods(["GET", "POST"])
def guest_lookup(request):
    order = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        pw   = request.POST.get("password", "").strip()
        if name and pw:
            # 같은 이름이 여러 건일 수 있으니 가장 최근 주문부터 검사
            for o in Order.objects.filter(user__isnull=True, guest_name=name).order_by("-id")[:20]:
                if o.check_guest_password(pw):
                    order = o
                    break
    return render(request, "orders/guest_lookup.html", {"order": order})
