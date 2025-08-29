from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import QuoteInquiry, QuoteComment

class QuoteInquiryForm(forms.ModelForm):
    class Meta:
        model = QuoteInquiry
        fields = ["title", "content", "attachment", "is_private"]
        widgets = {
            "content": SummernoteWidget(),  # 또는 SummernoteInplaceWidget()
            "is_private": forms.CheckboxInput(attrs={"class": "switch-input"}),
        }

class QuoteCommentForm(forms.ModelForm):
    class Meta:
        model = QuoteComment
        fields = ["content"]
        widgets = {
            "content": SummernoteWidget(attrs={"summernote": {"height": 220}}),
        }
