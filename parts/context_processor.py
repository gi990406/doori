from .models import CarManufacturer, PartSubCategory

def global_context(request):
    return {
        'manufacturers': CarManufacturer.objects.all(),
        'category_choices': PartSubCategory.PartsCategory.choices
    }
