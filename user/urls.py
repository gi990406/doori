from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('login/', views.login, name="login"),
    path("register/terms/", views.RegisterTermsView.as_view(), name="register_terms"),
    path('logout/', views.logout, name='logout'),
]
