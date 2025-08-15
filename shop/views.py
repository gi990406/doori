from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .cart import Cart
from parts.models import Part

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
