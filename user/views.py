from django.shortcuts import redirect

# 회원가입 import
from .forms import RegisterForm
from django.views.generic import CreateView
from .models import User
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from .models import Terms_and_condition

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