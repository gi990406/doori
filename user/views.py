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
from django.views.decorators.http import require_POST

from .forms import FindIDForm
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password
from .decorators import anonymous_required

from .forms import PasswordResetMatchForm, PasswordResetNewForm

from django.core.paginator import Paginator
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
# Create your views here..
class RegisterTermsView(TemplateView):
    template_name = "user/terms.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("index")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["terms_obj"] = Terms_and_condition.objects.order_by("-id").first()
        return ctx

    def post(self, request, *args, **kwargs):
        agree  = request.POST.get("agree") == "1"
        agree2 = request.POST.get("agree2") == "1"

        if not agree:
            messages.error(request, "회원가입약관의 내용에 동의하셔야 회원가입 하실 수 있습니다.")
            return self.get(request, *args, **kwargs)
        if not agree2:
            messages.error(request, "개인정보취급방침의 내용에 동의하셔야 회원가입 하실 수 있습니다.")
            return self.get(request, *args, **kwargs)

        # ✅ 약관 동의 성공 표시 후 회원가입 페이지로 리다이렉트 (GET)
        request.session["agreed_terms"] = True
        return redirect(reverse("user:register"))

class RegisterView(CreateView):
    model = User
    template_name = 'user/register.html'
    form_class = RegisterForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        # ✅ 약관 미동의 시 약관 페이지로
        if not request.session.get("agreed_terms"):
            return redirect("user:register_terms")
        # 원치 않으면 여기서 바로 지워도 됨
        # request.session.pop("agreed_terms", None)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        # 가입 완료 후 약관 플래그 제거
        self.request.session.pop("agreed_terms", None)
        messages.success(self.request, "회원가입 성공.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "입력값을 확인해 주세요.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('user:login')

def login(request):
    # 이미 로그인한 경우: 로그인 페이지 접근 차단
    if request.user.is_authenticated:
        return redirect('/')  # 또는 settings.LOGIN_REDIRECT_URL

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')

        user = authenticate(request, user_id=user_id, password=password)

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
        user = authenticate(request, user_id=request.user.user_id, password=pw)
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
    from shop.models import Order

    # (단가 × 수량) 라인 합
    line_total = ExpressionWrapper(
        F('items__unit_price') * F('items__quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=0)  # OrderItem.unit_price가 decimal_places=0
    )

    orders_qs = (
        Order.objects
        .filter(user=user)                # 게스트 주문까지 보여주려면 | Q(user__isnull=True, guest_email=user.email)
        .order_by('-created_at')
        .annotate(
            item_count=Coalesce(Sum('items__quantity'), 0),
            total_amount=Coalesce(Sum(line_total), Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)))
        )
    )

    page_obj = Paginator(orders_qs, 5).get_page(request.GET.get('page'))

    return render(request, "user/mypage.html", {
        "user_name": getattr(user, "name", None) or getattr(user, "user_id", ""),
        "user_email": user.email,
        "user_hp": getattr(user, "hp", ""),
        "date_joined": user.date_joined,
        "page_obj": page_obj,
    })

@login_required
@require_POST
def account_delete(request):
    user = request.user
    logout(request)
    user.is_active = False   # 완전 삭제하려면: user.delete()
    user.save()
    messages.success(request, '탈퇴가 완료되었습니다.')
    return redirect('index')


def _mask(s: str) -> str:
    """아이디 마스킹: abcd1234 -> ab***34"""
    if not s:
        return ""
    if len(s) <= 4:
        return s[0] + "***"
    return s[:2] + "***" + s[-2:]

@anonymous_required()
def find_id(request):
    """
    이름+이메일로 가입된 계정의 user_id 목록을 찾아
    마스킹하여 화면에 보여주고, 같은 내용으로 이메일도 발송.
    """
    if request.method == "POST":
        form = FindIDForm(request.POST)
        if form.is_valid():
            name  = form.cleaned_data["name"].strip()
            email = form.cleaned_data["email"].strip().lower()
            qs = User.objects.filter(is_active=True, name__iexact=name, email__iexact=email)

            user_ids = [u.user_id for u in qs if getattr(u, "user_id", None)]
            masked   = [_mask(uid) for uid in user_ids]

            # 메일은 존재/미존재 관계없이 같은 톤으로 응답 (정보유출 방지)
            try:
                subject = "[두리상사] 아이디 찾기 안내"
                if user_ids:
                    body = f"{name}님, 아래 아이디가 확인되었습니다.\n\n" + "\n".join(f"- {m}" for m in masked)
                else:
                    body = f"{name}님, 입력하신 정보로 가입된 계정을 찾지 못했습니다."
                send_mail(
                    subject,
                    body,
                    getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                    [email],
                    fail_silently=True,
                )
            except Exception:
                pass

            request.session["find_id_masked"] = masked
            return redirect("user:find_id_done")
    else:
        form = FindIDForm()

    return render(request, "user/find_id_form.html", {"form": form})

@anonymous_required()
def find_id_done(request):
    masked = request.session.pop("find_id_masked", [])
    return render(request, "user/find_id_done.html", {"masked": masked})

@anonymous_required()
@require_http_methods(["GET", "POST"])
def password_reset_match(request):
    """
    STEP 1: 아이디/이름/이메일/휴대폰이 모두 저장된 정보와 일치하는지 확인.
    일치하면 세션에 사용자 키를 저장하고 비밀번호 변경 페이지로 이동.
    """
    if request.method == "POST":
        form = PasswordResetMatchForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data["user_id"].strip()
            name    = form.cleaned_data["name"].strip()
            email   = form.cleaned_data["email"].strip().lower()
            hp      = form.cleaned_data["hp"].strip()

            # 모든 항목 일치하는 활성 사용자 1명 찾기 (대소문자 무시: email/name은 iexact)
            try:
                user = User.objects.get(
                    is_active=True,
                    user_id=user_id,
                    name__iexact=name,
                    email__iexact=email,
                    hp=hp,
                )
            except User.DoesNotExist:
                messages.error(request, "입력하신 정보가 일치하지 않습니다.")
            else:
                # ✅ 일치 → 세션에 통과 마크 후 다음 단계로
                request.session["pw_match_uid"] = user.pk
                return redirect("user:password_reset_match_new")
    else:
        form = PasswordResetMatchForm()

    return render(request, "user/password_reset_match.html", {"form": form})

@anonymous_required()
@require_http_methods(["GET", "POST"])
def password_reset_match_new(request):
    """
    STEP 2: 위 검증을 통과한 사용자에게 새 비밀번호 설정 폼 제공.
    """
    uid = request.session.get("pw_match_uid")
    if not uid:
        messages.error(request, "인증 세션이 만료되었습니다. 처음부터 다시 진행해 주세요.")
        return redirect("user:password_reset_match")

    try:
        user = User.objects.get(pk=uid, is_active=True)
    except User.DoesNotExist:
        messages.error(request, "인증 정보가 유효하지 않습니다.")
        return redirect("user:password_reset_match")

    if request.method == "POST":
        form = PasswordResetNewForm(request.POST)
        if form.is_valid():
            new_pw = form.cleaned_data["new_password1"]
            user.password = make_password(new_pw)
            user.save(update_fields=["password"])

            # 세션 정리
            request.session.pop("pw_match_uid", None)

            messages.success(request, "비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.")
            return redirect("user:login")
    else:
        form = PasswordResetNewForm()

    return render(request, "user/password_reset_match_new.html", {"form": form})
