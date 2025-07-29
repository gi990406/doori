from django.urls import path, re_path
from . import views

app_name = 'parts'

urlpatterns = [
    path('', views.ProductListView.as_view(), name="product_list"),
    path('manufacturer/<int:manufacturer_id>/', views.ProductListView.as_view(), name='product_by_manufacturer'),
]