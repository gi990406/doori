from django.urls import path, re_path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.NoticeListView.as_view(), name="notice_list"),
    re_path(r'^notice_(?P<pk>\d+)/$', views.notice_detail, name="notice_detail"),
]