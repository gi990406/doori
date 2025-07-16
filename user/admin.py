from django.contrib import admin
from .models import User, Terms_and_condition
from django.contrib.auth.models import Group
from django_summernote.admin import SummernoteModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
class UserAdmin(BaseUserAdmin):
    list_display = ('user_id', 'name', 'hp')
    search_fields = ('user_id', 'name', 'hp')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    fieldsets = (
    )

admin.site.register(User, UserAdmin)

admin.site.unregister(Group)

# Terms_and_condition 모델 등록
@admin.register(Terms_and_condition)
class Terms_and_conditionAdmin(SummernoteModelAdmin):
    summernote_fields = ['user_terms_and_conditions', 'privacy_policy']