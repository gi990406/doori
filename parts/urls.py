from django.urls import path, re_path
from . import views

app_name = 'parts'

urlpatterns = [
    path('', views.ProductListView.as_view(), name="product_list"),
    path('manufacturer/<int:manufacturer_id>/', views.ProductListView.as_view(), name='product_by_manufacturer'),
    path('model/<int:car_model_id>/', views.CarModelPartsListView.as_view(), name='product_by_model'),
    path('<int:pk>/detail/', views.ProductDetailView.as_view(), name='product_detail'),
    path('category/<str:category>/', views.ProductListView.as_view(), name='product_by_category'),
]
