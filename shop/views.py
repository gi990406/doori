from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .cart import Cart
from parts.models import Part
from django.views.decorators.http import require_http_methods
from .models import Order, OrderItem
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods
from django.db import transaction

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

    # 1) buy-now 파라미터는 GET/POST 모두에서 수집
    part_id = request.GET.get("part_id") or request.POST.get("part_id")
    try:
        qty = int(request.GET.get("qty") or request.POST.get("qty") or 1)
    except ValueError:
        qty = 1

    def build_item_from_part(p, q):
        price = getattr(p, "price", None)
        stock_ok = True
        if hasattr(p, "stock"):
            stock_ok = (p.stock or 0) >= q
        return {
            "product": p,
            "price": price,
            "qty": q,
            "stock_ok": stock_ok,
            "subtotal": (price or 0) * q,
        }

    # 2) 아이템 스냅샷: buy-now가 우선, 없으면 cart
    items, using_cart = [], True
    if part_id:
        p = get_object_or_404(Part, pk=part_id)
        items.append(build_item_from_part(p, qty))
        using_cart = False
    else:
        for it in cart:
            it.setdefault("subtotal", (it["price"] or 0) * it["qty"])
            items.append(it)

    has_inquiry = any(i["price"] is None for i in items)
    has_stock_issue = any(not i["stock_ok"] for i in items)
    total_amount = sum(i["subtotal"] for i in items)

    if request.method == "POST":
        if not items:
            messages.warning(request, "주문할 상품이 없습니다.")
            return redirect("shop:order_form")
        if has_inquiry or has_stock_issue:
            messages.error(request, "전화문의 상품 또는 재고 이슈가 있어 주문할 수 없습니다.")
            return redirect("shop:order_form")

        order = Order()
        if request.user.is_authenticated:
            order.user = request.user
            order.memo = request.POST.get("memo", "")
        else:
            order.guest_name  = request.POST.get("name", "").strip()
            order.guest_hp    = request.POST.get("hp", "").strip()
            order.guest_email = request.POST.get("email", "").strip()
            raw_pw = request.POST.get("password", "").strip()
            if not (order.guest_name and order.guest_hp and order.guest_email and raw_pw):
                messages.error(request, "비회원 주문의 필수 정보를 모두 입력해주세요.")
                if part_id:
                    return redirect(f"{reverse('shop:order_form')}?part_id={part_id}&qty={qty}")
                return redirect("shop:order_form")
            order.guest_password = make_password(raw_pw)
            order.memo = request.POST.get("memo", "")
        order.save()

        for i in items:
            p = i["product"]
            OrderItem.objects.create(
                order=order,
                part=p,
                title=getattr(p, "title", str(p)),
                unit_price=i["price"],
                quantity=i["qty"],
            )

        if using_cart:
            cart.clear()

        return redirect("shop:complete", order_id=order.id)

    ctx = {
        "is_member": request.user.is_authenticated,
        "items": items,
        "total_amount": total_amount,
        "using_cart": using_cart,
        "buy_now_part_id": part_id,
        "buy_now_qty": qty,
    }
    if request.user.is_authenticated:
        ctx.update({
            "default_name":  getattr(request.user, "name", ""),
            "default_hp":    getattr(request.user, "hp", ""),
            "default_email": getattr(request.user, "email", ""),
        })
    return render(request, "orders/order_form.html", ctx)

@require_POST
@transaction.atomic
def order_create(request):
    is_member = request.user.is_authenticated

    # 1) 주문 기본 정보
    if is_member:
        order = Order.objects.create(
            user=request.user,
            memo=request.POST.get("memo", "")
        )
    else:
        guest_name  = request.POST.get("guest_name", "").strip()
        guest_hp    = request.POST.get("guest_hp", "").strip()
        guest_email = request.POST.get("guest_email", "").strip()
        guest_pw    = request.POST.get("guest_password", "")

        if not (guest_name and guest_hp and guest_email and guest_pw):
            messages.error(request, "비회원 정보가 누락되었습니다.")
            return redirect("shop:order_form")

        order = Order.objects.create(
            user=None,
            guest_name=guest_name,
            guest_hp=guest_hp,
            guest_email=guest_email,
            guest_password=make_password(guest_pw),
            memo=request.POST.get("memo", "")
        )

    # 2) 아이템 구성 (바로구매 또는 장바구니)
    part_id = request.POST.get("part_id")
    qty     = int(request.POST.get("qty") or 1)

    if part_id:  # 바로구매
        part = get_object_or_404(Part, pk=part_id)
        unit_price = None if (getattr(part, "price", 0) in [None, 0]) else int(part.price)
        OrderItem.objects.create(
            order=order,
            part=part,
            title=getattr(part, "title", str(part)),
            unit_price=unit_price,  # None이면 전화문의
            quantity=qty,
        )
    else:
        # TODO: 장바구니에서 가져오는 로직 연결
        # for ci in cart_items:
        #     OrderItem.objects.create(order=order, part=ci.part, title=ci.part.title,
        #                              unit_price=ci.part.price or None, quantity=ci.qty)
        pass

    # 3) 완료 페이지로 이동(또는 결제 페이지)
    messages.success(request, "주문이 접수되었습니다.")
    return redirect("shop:order_complete", order_id=order.id)

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
