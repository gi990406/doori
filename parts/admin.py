from django.contrib import admin
from .models import CarManufacturer, CarModel, PartSubCategory, Part, PartImage, CarModelDetail
from django_summernote.admin import SummernoteModelAdmin

@admin.register(CarManufacturer)
class CarManufacturerAdmin(admin.ModelAdmin):
    """자동차 회사 관리"""
    list_display = ['name', 'is_imported']
    list_filter = ['is_imported']
    search_fields = ['name']

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    """차량 모델 관리"""
    list_display = ['name', 'manufacturer']
    list_filter = ['manufacturer']
    search_fields = ['name', 'manufacturer__name']
    autocomplete_fields = ['manufacturer']

@admin.register(CarModelDetail)
class CarModelDetailAdmin(admin.ModelAdmin):
    """차량 모델 관리"""
    list_display = ['name', 'model']
    list_filter = ['model']
    search_fields = ['name', 'model__name']
    autocomplete_fields = ['model']

@admin.register(PartSubCategory)
class PartSubCategoryAdmin(admin.ModelAdmin):
    """부품 카테고리 관리"""
    list_display = ['name', 'parent_category']
    list_filter = ['parent_category']
    search_fields = ['name']

class PartImageInline(admin.TabularInline):
    model = PartImage
    extra = 1

@admin.register(Part)
class PartAdmin(SummernoteModelAdmin):
    """부품 관리"""

    summernote_fields = ('description',)

    list_display = [
        'title',
        'part_number',
        'get_manufacturer',
        'get_car_model',
        'get_car_model_detail',
        'subcategory',
        'applicable_years',
        'stock',
        'price'
    ]
    list_filter = ['subcategory__parent_category', 'subcategory__name', 'car_model__manufacturer',]
    search_fields = ['title', 'part_number', 'car_model__name', 'car_model__manufacturer__name']
    autocomplete_fields = ['car_model', 'subcategory', 'car_model_detail']
    inlines = [PartImageInline]
    list_editable = ['stock']

    def get_car_model(self, obj):
        return obj.car_model.name if obj.car_model else None
    get_car_model.short_description = "모델명"

    def get_manufacturer(self, obj):
        return obj.car_model.manufacturer.name if obj.car_model else None
    get_manufacturer.short_description = "제조사"

    def get_car_model_detail(self, obj):
        return obj.car_model_detail.name if obj.car_model_detail else None
    get_car_model_detail.short_description = "세부 차종명"
