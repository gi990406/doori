from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path("cart/", views.cart_detail, name="cart_detail"),
    path("add/<int:part_id>/", views.cart_add, name="add"),
    path("update/<int:part_id>/", views.cart_update, name="update"),
    path("remove/<int:part_id>/", views.cart_remove, name="remove"),
]
