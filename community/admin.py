from django.contrib import admin
from . import models
from django_summernote.admin import SummernoteModelAdmin

# Register your models here.
class ImageInline(admin.TabularInline):
    model = models.Notice_Image
    extra = 1

@admin.register(models.Notice)
class NoticeAdmin(SummernoteModelAdmin):
    inlines = [ImageInline]
    summernote_fields = ['content',]
