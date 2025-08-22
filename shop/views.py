from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .cart import Cart
from parts.models import Part
from django.views.decorators.http import require_http_methods
from .models import Order, OrderItem
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import json

@require_POST
def cart_update_ajax(request):
    """
    요청: {product_id:int, qty:int}
    응답: {
      ok:bool, qty:int, item_subtotal:int, cart_total:int,
      stock:int|null, stock_ok:bool|null,
      has_inquiry_only:bool, has_stock_issue:bool
    }
    """
    try:
      payload = json.loads(request.body.decode())
      product_id = int(payload.get("product_id"))
      qty = max(1, int(payload.get("qty", 1)))
    except Exception:
      return JsonResponse({"ok": False, "error": "잘못된 요청"}, status=400)

    # 장바구니/상품 로직은 프로젝트에 맞게 바꿔주세요
    cart = request.cart  # 미들웨어나 헬퍼로 세션 카트 접근한다고 가정
    item = cart.update(product_id=product_id, qty=qty)   # 수량 갱신
    cart.recalculate()                                   # 합계/상태 갱신

    return JsonResponse({
        "ok": True,
        "qty": item.qty,
        "item_subtotal": int(item.subtotal or 0),
        "cart_total": int(cart.total or 0),
        "stock": item.stock if item.stock is not None else None,
        "stock_ok": bool(item.stock_ok) if item.stock is not None else None,
        "has_inquiry_only": bool(cart.has_inquiry_only),
        "has_stock_issue": bool(cart.has_stock_issue),
    })

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
    if has_inquiry or has_stock_issue:
        messages.error(request, "전화문의 상품 또는 재고 이슈가 있어 주문할 수 없습니다.")

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

def buy_now(request, part_id):
    part = get_object_or_404(Part, pk=part_id)

    # ① 전화문의/가격 0 → 주문 불가
    if part.price in (None, 0, "0", ""):
        messages.error(request, "전화문의 상품은 주문서로 바로 진행할 수 없습니다. 문의하기로 진행해주세요.")
        return redirect("shop:product_detail", part_id=part.id)

    # ② 재고 체크
    if part.stock is not None and int(part.stock) < 1:
        messages.error(request, "재고가 없어 주문할 수 없습니다.")
        return redirect("shop:product_detail", part_id=part.id)

    # ③ 장바구니 정리 후 1개 담고 주문서로
    cart = Cart(request)
    cart.clear()                      # 기존 담긴 것 비우고
    cart.add(part_id, qty=1)          # 수량 조절 원하면 ?qty= 파라미터로 받아 처리

    # 주문서로 이동 (네임스페이스 확인: order:order_form or shop:order_form)
    return redirect("shop:order_form")
