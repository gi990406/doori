from functools import wraps
from django.shortcuts import redirect, resolve_url

def anonymous_required(redirect_url="index"):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_authenticated:
                return redirect(resolve_url(redirect_url))
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
