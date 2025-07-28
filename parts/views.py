from django.views.generic import ListView
from .models import Part
from django.shortcuts import get_object_or_404, render

# Create your views here.
class ProductListView(ListView):
    """제품 목록"""
    model = Part
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    ordering = ['-id']
    paginate_by = 10

    def get_queryset(self):
        queryset = Part.objects.prefetch_related('images').order_by('-id')

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
