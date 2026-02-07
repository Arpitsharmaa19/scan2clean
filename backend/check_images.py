import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reports.models import WasteReport

reports = WasteReport.objects.order_by('-id')[:5]
for r in reports:
    print(f"ID: {r.id}, Status: {r.status}, Image: {r.image}, URL: {r.image.url if r.image else 'None'}")
