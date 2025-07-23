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
    paginate_by = 10

    def get_queryset(self):
        queryset = Notice.objects.prefetch_related('images').order_by('-created_at', '-id')

        return queryset

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        # 페이징 처리
        paginator = context['paginator']
        page_numbers_range = 5
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range

        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range

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