from django.urls import path, reverse_lazy

from . import views
from django.contrib.auth import views as auth_views

app_name = 'user'

urlpatterns = [
    path('login/', views.login, name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("register/terms/", views.RegisterTermsView.as_view(), name="register_terms"),
    path("password/confirm/", views.password_confirm, name="password_confirm"),
    path("user/edit/", views.profile_edit, name="profile_edit"),
    path("mypage/", views.mypage, name="mypage"),
    path('logout/', views.logout, name='logout'),
    path("account/delete/", views.account_delete, name="account_delete"),

    path("find-id/", views.find_id, name="find_id"),
    path("find-id/done/", views.find_id_done, name="find_id_done"),

     # ── ✨ “보유 정보 일치” 비밀번호 재설정 (새로 추가) ──
    path("password-reset/match/", views.password_reset_match, name="password_reset_match"),
    path("password-reset/match/new/", views.password_reset_match_new, name="password_reset_match_new"),
]
