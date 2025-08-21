from django.views.generic import ListView
from .models import Notice
from django.shortcuts import get_object_or_404, render

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
