from django.shortcuts import redirect, resolve_url

class AnonymousRequiredMixin:
    """로그인 된 사용자는 접근 금지하고 다른 곳으로 보냄."""
    redirect_url = "index"  # 원하는 URL name으로 수정 가능

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(resolve_url(self.redirect_url))
        return super().dispatch(request, *args, **kwargs)
