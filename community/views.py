from django.views.generic import ListView, DetailView, CreateView
from .models import Notice
from django.shortcuts import get_object_or_404, render, redirect
from .forms import QuoteInquiryForm, QuoteCommentForm
from .models import QuoteInquiry
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .forms import QuoteCommentForm

# Create your views here.
class NoticeListView(ListView):
    """공지 목록"""
    model = Notice
    template_name = 'community/notice_list.html'
    context_object_name = 'notices'
    ordering = ['-created_at', '-id']
    paginate_by = 5

    def get_queryset(self):
        queryset = Notice.objects.prefetch_related('images').order_by('-created_at', '-id')

        return queryset

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        if context.get('is_paginated'):
            paginator = context['paginator']
            page_obj  = context['page_obj']
            window = 5
            current = page_obj.number
            start = ((current - 1) // window) * window + 1
            end = min(start + window - 1, paginator.num_pages)
            context['page_range'] = range(start, end + 1)

        return context

def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    prev_notice = Notice.objects.filter(id__lt=notice.id).order_by('-id').first()

    notice.hits += 1
    notice.save(update_fields=['hits'])

    context = {
        'notice': notice,
        'prev_notice' : prev_notice,
    }

    return render(request, 'community/notice_detail.html', context)

class InquiryListView(ListView):
    model = QuoteInquiry
    paginate_by = 10
    template_name = "community/inquiry_list.html"

    def get_queryset(self):
        qs = QuoteInquiry.objects.all()
        u = self.request.user
        if u.is_staff:
            return qs
        if u.is_authenticated:
            return qs.filter(Q(is_private=False) | Q(user=u))
        return qs.filter(is_private=False)

# 2) 작성: 로그인 필요 (그대로)
class InquiryCreateView(CreateView):
    model = QuoteInquiry
    form_class = QuoteInquiryForm
    template_name = "community/inquiry_form.html"
    success_url = reverse_lazy("community:quotes_list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "견적 문의가 등록되었습니다.")
        return super().form_valid(form)

# 3) 상세: 익명/타인 = 공개글만 조회 가능
class InquiryDetailView(DetailView):
    model = QuoteInquiry
    template_name = "community/inquiry_detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff:
            return qs
        if u.is_authenticated:
            return qs.filter(Q(is_private=False) | Q(user=u))
        return qs.filter(is_private=False)

@login_required
@user_passes_test(lambda u: u.is_staff)
def create_comment(request, pk):
    inquiry = get_object_or_404(QuoteInquiry, pk=pk)
    if request.method == "POST":
        form = QuoteCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.inquiry = inquiry
            comment.author = request.user
            comment.is_from_admin = True
            comment.save()
            # 상태 자동 변경
            if inquiry.status == QuoteInquiry.Status.OPEN:
                inquiry.status = QuoteInquiry.Status.ANSWERED
                inquiry.save(update_fields=["status"])
            messages.success(request, "답변이 등록되었습니다.")
    return redirect("community:quotes_detail", pk=pk)

@login_required
def close_inquiry(request, pk):
    inquiry = get_object_or_404(QuoteInquiry, pk=pk, user=request.user)
    inquiry.status = QuoteInquiry.Status.CLOSED
    inquiry.save(update_fields=["status"])
    messages.success(request, "문의가 종결되었습니다.")
    return redirect("community:quotes_detail", pk=pk)
