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

# 로그인 import
from django.contrib.auth import authenticate, logout as logout_user, login as auth_login

# Create your views here.
class RegisterView(CreateView):
    """회원가입"""
    model = User
    template_name = 'user/register.html'
    form_class = RegisterForm

    def get(self, request, *args, **kwargs):
        url = settings.LOGIN_REDIRECT_URL
        if request.user.is_authenticated:
            return HttpResponseRedirect(url)
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "회원가입 성공.")
        return reverse('user:login')

    def form_valid(self, form):
        self.object = form.save()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terms'] = Terms_and_condition.objects.filter(id=1).get()

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

def logout(request):
    logout_user(request)
    return redirect('/')
