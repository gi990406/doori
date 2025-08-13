from django.shortcuts import redirect, render

# 회원가입 import
from .forms import RegisterForm
from django.views.generic import CreateView
from .models import User
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from .models import Terms_and_condition
from django.views.generic import TemplateView

# 로그인 import
from django.contrib.auth import authenticate, logout as logout_user, login as auth_login

from django.contrib.auth.decorators import login_required
from django.utils.http import urlencode
from .forms import ProfileEditForm
from urllib.parse import urlparse

# Create your views here..
class RegisterTermsView(TemplateView):
    template_name = "user/terms.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("index")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["terms_obj"] = Terms_and_condition.objects.order_by("-id").first()
        return context

    def post(self, request, *args, **kwargs):
        agree = request.POST.get("agree")
        agree2 = request.POST.get("agree2")

        if not agree:
            messages.error(request, "회원가입약관의 내용에 동의하셔야 회원가입 하실 수 있습니다.")
            return self.get(request, *args, **kwargs)
        if not agree2:
            messages.error(request, "개인정보취급방침의 내용에 동의하셔야 회원가입 하실 수 있습니다.")
            return self.get(request, *args, **kwargs)

        return redirect("/")

class RegisterView(CreateView):
    """회원가입"""
    model = User
    template_name = 'user/register.html'
    form_class = RegisterForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "회원가입 성공.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "입력값을 확인해 주세요.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('user:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def login(request):
    # 이미 로그인한 경우: 로그인 페이지 접근 차단
    if request.user.is_authenticated:
        return redirect('/')  # 또는 settings.LOGIN_REDIRECT_URL

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')

        user = authenticate(request, username=user_id, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('/')  # ✅ 홈 URL name
        elif user_id == '':
            return render(request, 'user/login.html', {'error': '아이디를 입력해주세요.'})
        elif password == '':
            return render(request, 'user/login.html', {'error': '비밀번호를 입력해주세요.'})
        else:
            return render(request, 'user/login.html', {'error': '아이디 또는 비밀번호가 잘못되었습니다.'})

    return render(request, 'user/login.html')

@login_required
def password_confirm(request):
    """
    회원 정보 변경 등 민감 페이지 진입 전 비밀번호 확인.
    성공 시 세션 플래그를 세팅하고 next로 리디렉션.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('user:profile_edit')  # 원하는 기본 목적지로 교체

    parsed = urlparse(next_url)
    if parsed.netloc:
        next_url = reverse('user:profile_edit')

    if request.method == "POST":
        pw = request.POST.get("password", "")
        user = authenticate(request, username=request.user.user_id, password=pw)
        if user is not None:
            # 5분만 유효한 플래그
            request.session["pw_confirm_ok"] = True
            request.session.set_expiry(300)
            return redirect(next_url)
        messages.error(request, "비밀번호가 일치하지 않습니다.")

    return render(request, "user/change_verification.html", {"next": next_url})

@login_required
def profile_edit(request):
    # 비밀번호 재확인 통과 여부 확인
    if not request.session.get("pw_confirm_ok"):
        return redirect(f"{reverse('user:password_confirm')}?{urlencode({'next': request.get_full_path()})}")

    user = request.user
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # 한 번 통과했으면 플래그 제거(원하면 유지 가능)
            request.session.pop("pw_confirm_ok", None)
            messages.success(request, "회원 정보가 수정되었습니다.")
            return redirect(reverse("index"))
        else:
            messages.error(request, "입력값을 확인해 주세요.")
    else:
        form = ProfileEditForm(instance=user)

    context = {
        "form": form,
        "user_id": user.user_id,  # 읽기전용 표시용
        "name": user.name,        # 읽기전용 표시용
    }
    return render(request, "user/profile_edit.html", context)

def logout(request):
    logout_user(request)
    return redirect('/')

@login_required(login_url='user:login')
def mypage(request):
    user = request.user

    # 최근 주문/보관함: 아직 모델이 없다면 빈 리스트로
    recent_orders = []
    recent_wishlist = []

    # (주문/보관 모델이 생기면 아래 패턴으로 교체)
    # from orders.models import Order
    # recent_orders = Order.objects.filter(user=user).order_by("-created_at")[:5]
    # from shop.models import Wishlist
    # recent_wishlist = Wishlist.objects.filter(user=user).select_related("product").order_by("-created_at")[:5]

    context = {
        "user_name": user.name or user.user_id,
        "user_email": user.email,
        "user_hp": user.hp,
        "date_joined": user.date_joined,
        "recent_orders": recent_orders,
        "recent_wishlist": recent_wishlist,
    }
    return render(request, "user/mypage.html", context)


@login_required
def account_delete(request):
    if request.method == 'POST':
        # 실제 탈퇴 처리(비활성화 or 삭제)
        user = request.user
        from django.contrib.auth import logout
        logout(request)
        user.is_active = False  # 또는 user.delete()
        user.save()
        messages.success(request, '탈퇴가 완료되었습니다.')
        return redirect('index')
    return render(request, 'user/account_delete_confirm.html')
