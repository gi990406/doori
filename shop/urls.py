from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path("cart/", views.cart_detail, name="cart_detail"),
    path("add/<int:part_id>/", views.cart_add, name="add"),
    path("update/<int:part_id>/", views.cart_update, name="update"),
    path("remove/<int:part_id>/", views.cart_remove, name="remove"),

    path("order/", views.order_form, name="order_form"),                 # 회원/비회원 공용 시작
    path("complete/<int:order_id>/", views.order_complete, name="complete"),
    path("guest-lookup/", views.guest_lookup, name="guest_lookup"),
]
