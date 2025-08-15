# cart/cart.py
from decimal import Decimal
from django.conf import settings
from parts.models import Part   # ← 반드시 Part로!

CART_SESSION_ID = getattr(settings, "CART_SESSION_ID", "cart")

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, part_id, qty=1, replace=False):
        pid = str(part_id)
        if pid not in self.cart:
            self.cart[pid] = {"qty": 0}
        if replace:
            self.cart[pid]["qty"] = int(qty)
        else:
            self.cart[pid]["qty"] += int(qty)
        if self.cart[pid]["qty"] <= 0:
            del self.cart[pid]
        self.save()

    def remove(self, part_id):
        pid = str(part_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        pids = list(self.cart.keys())
        parts = Part.objects.filter(id__in=pids)      # ← Part로 조회
        pmap = {str(p.id): p for p in parts}

        for pid in pids:
            part = pmap.get(pid)
            if not part:
                # 삭제되었거나 없는 부품은 세션에서 제거
                del self.cart[pid]
                self.save()
                continue

            qty = int(self.cart[pid]["qty"])
            # 가격 필드명에 맞게 수정 (price가 아니라면 여기 바꾸세요)
            raw_price = getattr(part, "price", None)

            # 0 또는 None이면 '전화문의' 취급
            if raw_price in (None, 0, "0", ""):
                price = None
            else:
                price = Decimal(raw_price)

            subtotal = Decimal("0") if price is None else price * qty

            stock = getattr(part, "stock", None)
            stock_ok = True if (stock is None or qty <= stock) else False

            yield {
                "product": part,     # ← 템플릿의 p=item.product 와 일치!
                "qty": qty,
                "price": price,
                "subtotal": subtotal,
                "stock": stock,
                "stock_ok": stock_ok,
            }

    def total(self):
        t = Decimal("0")
        for item in self:
            t += item["subtotal"]
        return t

    def has_inquiry_only(self):
        return any(item["price"] is None for item in self)

    def has_stock_issue(self):
        return any(not item["stock_ok"] for item in self)

    def save(self):
        self.session.modified = True
