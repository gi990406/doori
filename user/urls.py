from django.urls import path
from . import views

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
]
