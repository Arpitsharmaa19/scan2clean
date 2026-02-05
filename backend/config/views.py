from django.shortcuts import render
from django.contrib.auth import get_user_model
from reports.models import WasteReport

User = get_user_model()

def home(request):
    try:
        total_resolved = WasteReport.objects.filter(status='resolved').count()
        total_citizens = User.objects.count()
        total_reports = WasteReport.objects.count()
        
        # Calculate cleanup rate
        cleanup_rate = 100 if total_reports == 0 else int((total_resolved / total_reports) * 100)
    except Exception:
        # Fallback if DB is not ready or any other issue
        total_resolved = 0
        total_citizens = 0
        total_reports = 0
        cleanup_rate = 0
    
    return render(request, 'home.html', {
        'total_resolved': total_resolved,
        'total_citizens': total_citizens,
        'cleanup_rate': cleanup_rate,
        'total_reports': total_reports
    })
