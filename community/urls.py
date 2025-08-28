from django.urls import path, re_path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.NoticeListView.as_view(), name="notice_list"),
    re_path(r'^notice_(?P<pk>\d+)/$', views.notice_detail, name="notice_detail"),
    path("quotes/", views.InquiryListView.as_view(), name="quotes_list"),
    path("quotes/new/", views.InquiryCreateView.as_view(), name="quotes_create"),
    path("quotes/<int:pk>/", views.InquiryDetailView.as_view(), name="quotes_detail"),
    path("quotes/<int:pk>/comment/", views.create_comment, name="comment_create"),
    path("quotes/<int:pk>/close/", views.close_inquiry, name="close"),  # 선택: 종결
]
