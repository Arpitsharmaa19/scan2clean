"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""




from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

from django.conf import settings
from django.conf.urls.static import static


from reports.models import WasteReport
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    total_resolved = WasteReport.objects.filter(status='resolved').count()
    total_citizens = User.objects.count()
    total_reports = WasteReport.objects.count()
    
    # Calculate cleanup rate
    cleanup_rate = 100 if total_reports == 0 else int((total_resolved / total_reports) * 100)
    
    return render(request, 'home.html', {
        'total_resolved': total_resolved,
        'total_citizens': total_citizens,
        'cleanup_rate': cleanup_rate,
        'total_reports': total_reports
    })


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page
    path('', home, name='home'),

    # Auth + dashboard routes
    path('', include('accounts.urls')),

    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
    path('api/', include('config.api_urls')),

]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


