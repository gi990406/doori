from django.shortcuts import render
from community.models import Notice
from parts.models import Part

def home(request):

    notices = Notice.objects.prefetch_related('images').all().order_by('-created_at')[:3]
    parts = Part.objects.prefetch_related('images').all().order_by('-id')[:25]

    for part in parts:
        try:
            part.formatted_price = "{:,.0f}".format(part.price)
        except (ValueError, TypeError):
            part.formatted_price = part.price

    return render(request, 'index.html', {'notices': notices, 'parts': parts})
