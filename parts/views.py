from django.views.generic import ListView, DetailView
from .models import Part, CarModel, CarManufacturer, PartSubCategory, CarModelDetail
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
        category = self.kwargs.get('category')
        self.category = self.kwargs.get('category')

        queryset = Part.objects.select_related('car_model__manufacturer', 'subcategory').prefetch_related('images').order_by('-id')
        manufacturer_id = self.kwargs.get('manufacturer_id')

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
            context['subcategory_list'] = PartSubCategory.objects.filter(parent_category=self.category).annotate(part_count=Count('part'))
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
        context['model_details'] = (CarModelDetail.objects
                                    .filter(model=self.car_model)
                                    .annotate(part_count=Count('parts')))
        return context

class ProductByModelDetailView(ListView):
    """특정 세부차종의 부품 목록"""
    model = Part
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    ordering = ['-id']

    def get_queryset(self):
        self.detail = get_object_or_404(CarModelDetail, id=self.kwargs['detail_id'])
        qs = Part.objects.select_related('car_model__manufacturer', 'subcategory', 'car_model_detail')\
                         .prefetch_related('images')\
                         .filter(car_model_detail=self.detail)\
                         .order_by('-id')
        for p in qs:
            try:
                p.formatted_price = "{:,.0f}".format(p.price)
            except Exception:
                p.formatted_price = p.price
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_manufacturer'] = self.detail.model.manufacturer.name
        context['selected_model'] = self.detail.model.name
        context['selected_model_detail'] = self.detail.name
        # 같은 모델의 다른 세부차종들(탭 전환용)
        context['model_details'] = CarModelDetail.objects.filter(model=self.detail.model)\
                                .annotate(part_count=Count('parts'))
        context['category_choices'] = PartSubCategory.PartsCategory.choices
        return context


class ProductBySubcategoryView(ListView):
    """세부 카테고리별 제품 목록"""
    model = Part
    template_name = 'product/subcategory_list.html'
    context_object_name = 'products'
    ordering = ['-id']

    def get_queryset(self):
        self.subcategory = get_object_or_404(PartSubCategory, id=self.kwargs['subcategory_id'])
        self.parent_category = self.subcategory.get_parent_category_display()

        queryset = Part.objects.select_related('car_model__manufacturer', 'subcategory') \
                               .prefetch_related('images') \
                               .filter(subcategory=self.subcategory) \
                               .order_by('-id')

        for part in queryset:
            try:
                part.formatted_price = "{:,.0f}".format(part.price)
            except (ValueError, TypeError):
                part.formatted_price = part.price

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_subcategory'] = self.subcategory
        context['selected_subcategory_display'] = str(self.subcategory.name)
        context['selected_parent_category_display'] = self.parent_category  # ✅ 추가

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

