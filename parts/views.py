from django.views.generic import ListView, DetailView
from .models import Part, CarModel, CarManufacturer, PartSubCategory
from django.shortcuts import get_object_or_404, render
from django.db.models import Count

# Create your views here.
class ProductListView(ListView):
    """제품 목록"""
    model = Part
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    ordering = ['-id']
    paginate_by = 10

    def get_queryset(self):
        self.manufacturer = None
        self.category = None

        queryset = Part.objects.select_related('car_model__manufacturer', 'subcategory').prefetch_related('images').order_by('-id')
        manufacturer_id = self.kwargs.get('manufacturer_id')
        category = self.kwargs.get('category')

        if manufacturer_id:
            self.manufacturer = get_object_or_404(CarManufacturer, id=manufacturer_id)
            queryset = queryset.filter(car_model__manufacturer=self.manufacturer)

        if category:
            queryset = queryset.filter(subcategory__parent_category=category)

        for part in queryset:
            try:
                part.formatted_price = "{:,.0f}".format(part.price)
            except (ValueError, TypeError):
                part.formatted_price = part.price

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

        # 선택된 제조사
        if self.manufacturer:
            context['selected_manufacturer'] = self.manufacturer.name
            context['manufacturer_models'] = CarModel.objects.filter(manufacturer=self.manufacturer).annotate(part_count=Count('parts'))
        else:
            context['selected_manufacturer'] = None
            context['manufacturer_models'] = []

        # 카테고리 목록 (한글 변환용)
        context['selected_category'] = self.kwargs.get('category')
        context['category_choices'] = PartSubCategory.PartsCategory.choices
        context['selected_category_display'] = dict(PartSubCategory.PartsCategory.choices).get(self.kwargs.get('category'), "")

        # 선택된 대분류 카테고리
        context['selected_category'] = self.category
        context['selected_category_display'] = dict(PartSubCategory.PartsCategory.choices).get(self.category, "")

        # ✅ 세부 카테고리 목록 추가
        if self.category:
            context['subcategory_list'] = PartSubCategory.objects.filter(parent_category=self.category)
        else:
            context['subcategory_list'] = []

        return context

class CarModelPartsListView(ListView):
    """차종별 부품 리스트"""
    model = Part
    template_name = 'product/product_model_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        self.car_model = get_object_or_404(CarModel, id=self.kwargs['car_model_id'])

        queryset = Part.objects.filter(car_model=self.car_model).select_related('subcategory').prefetch_related('images')

        for part in queryset:
            try:
                part.formatted_price = "{:,.0f}".format(part.price)
            except (ValueError, TypeError):
                part.formatted_price = part.price

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['car_model'] = self.car_model
        return context

class ProductDetailView(DetailView):
    model = Part
    template_name = 'product/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        part = self.object
        if part.price:
            context['formatted_price'] = "{:,.0f}".format(part.price)
        else:
            context['formatted_price'] = "전화문의"

        return context
