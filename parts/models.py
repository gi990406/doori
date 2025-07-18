from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class CarManufacturer(models.Model):
    """자동차 회사"""
    name = models.CharField(max_length=100, verbose_name="자동차 회사명")
    is_imported = models.BooleanField(default=False, verbose_name="수입자동차 여부")  # 수입 여부

    class Meta:
        verbose_name = "자동차 회사 관리"
        verbose_name_plural = "자동차 회사 관리"

    def __str__(self):
        return self.name

class CarModel(models.Model):
    manufacturer = models.ForeignKey(CarManufacturer, on_delete=models.CASCADE, related_name='models', verbose_name="자동차 회사")
    name = models.CharField(max_length=100, verbose_name="차량 모델")

    class Meta:
        verbose_name = "차량 모델"
        verbose_name_plural = "차량 모델 관리"

    def __str__(self):
        return f"{self.manufacturer.name} - {self.name}"
    
class PartSubCategory(models.Model):
    # 부품 카테고리
    class PartsCategory(models.TextChoices):
        FRONT = "front", _("전면")
        REAR = "rear", _("후면")
        SIDE = "side", _("측면")
        INTERIOR = "interior", _("실내")
        WHEEL = "wheel", _("중고순정휠")
        UNDERBODY = "underbody", _("하체")
        ETC = "etc", _("기타")

    parent_category = models.CharField(
        max_length=20,
        choices=PartsCategory.choices,
        verbose_name="부품 카테고리1"
    )

    name = models.CharField(max_length=100, verbose_name="부품 카테고리2")

    class Meta:
        verbose_name = "부품 카테고리"
        verbose_name_plural = "부품 카테고리"

    def __str__(self):
        return f"{self.get_parent_category_display()} - {self.name}"
    
class Part(models.Model):
    title = models.CharField(max_length=200, verbose_name="제목")

    car_model = models.ForeignKey(CarModel, on_delete=models.SET_NULL, related_name='parts', null=True, blank=True, verbose_name="차량 모델")

    part_number = models.CharField(max_length=256, verbose_name="제품번호")  # 품번
    applicable_years = models.CharField(max_length=50, help_text="예: 2015-2018", verbose_name="연식")

    # 카테고리
    subcategory = models.ForeignKey(PartSubCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="부품 카테고리")

    stock = models.PositiveIntegerField(default=0, verbose_name="재고")
    price = models.DecimalField(max_digits=10, decimal_places=0, null=True, verbose_name="가격")
    description = models.TextField(blank=True, verbose_name="유의사항")

    def __str__(self):
        return f"{self.title} ({self.part_number})"
    
    class Meta:
        verbose_name = "부품"
        verbose_name_plural = "부품 관리"

    def get_category_display(self):
        return self.subcategory.get_parent_category_display() if self.subcategory else None
    
class PartImage(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='images')

    def image_upload_path(instance, filename):
        return f"{instance.part.car_model.manufacturer.name}/{instance.part.car_model.name}/{instance.part.subcategory}/{filename}"

    image = models.ImageField(upload_to=image_upload_path)