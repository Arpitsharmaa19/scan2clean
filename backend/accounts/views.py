from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Count
import json

from .forms import LoginForm, CitizenRegisterForm
from reports.models import WasteReport
from notifications.models import Notification

User = get_user_model()

# =========================
# DASHBOARD REDIRECT
# =========================

@login_required
def redirect_dashboard(request):
    user = request.user

    if user.role == 'citizen':
        return redirect('citizen_dashboard')
    elif user.role == 'worker':
        return redirect('worker_dashboard')
    elif user.role == 'admin':
        return redirect('admin_dashboard')
    else:
        return HttpResponse("Invalid role")


# =========================
# 👤 CITIZEN DASHBOARD
# =========================

@login_required
def citizen_dashboard(request):
    user = request.user

    total_reports = WasteReport.objects.filter(citizen=user).count()
    pending_reports = WasteReport.objects.filter(
        citizen=user, status="pending"
    ).count()
    resolved_reports = WasteReport.objects.filter(
        citizen=user, status="resolved"
    ).count()

    recent_reports = WasteReport.objects.filter(
        citizen=user
    ).order_by("-created_at")[:5]

    # Tasks needing OTP verification
    verifying_reports = WasteReport.objects.filter(
        citizen=user, 
        status="assigned",
        verification_otp__isnull=False
    )

    # Resolved tasks needing rating
    unrated_reports = WasteReport.objects.filter(
        citizen=user,
        status="resolved",
        rating__isnull=True
    ).order_by("-resolved_at")[:3]
    
    assigned_reports = WasteReport.objects.filter(
        citizen=user, status="assigned"
    ).count()

    notifications = user.notifications.filter(is_read=False)[:5]

    return render(request, "dashboards/citizen_dashboard.html", {
        "total_reports": total_reports,
        "pending_reports": pending_reports,
        "resolved_reports": resolved_reports,
        "assigned_reports": assigned_reports,
        "recent_reports": recent_reports,
        "notifications": notifications,
        "verifying_reports": verifying_reports,
        "unrated_reports": unrated_reports,
        "test_mark": "RELOADED",
    })


# =========================
# 🛠️ ADMIN DASHBOARD
# =========================

@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("/dashboard/citizen/")

    # 📊 STATS
    total_users = User.objects.count()
    total_reports = WasteReport.objects.count()
    pending_reports = WasteReport.objects.filter(status="pending").count()
    assigned_reports = WasteReport.objects.filter(status="assigned").count()
    resolved_reports = WasteReport.objects.filter(status="resolved").count()

    # 📈 CHART DATA
    waste_data = (
        WasteReport.objects
        .values("waste_type")
        .annotate(count=Count("id"))
    )

    waste_labels = [w["waste_type"].title() for w in waste_data]
    waste_values = [w["count"] for w in waste_data]

    return render(request, "dashboards/admin_dashboard.html", {
        "total_users": total_users,
        "total_reports": total_reports,
        "pending_reports": pending_reports,
        "assigned_reports": assigned_reports,
        "resolved_reports": resolved_reports,
        "waste_labels": json.dumps(waste_labels),
        "waste_values": json.dumps(waste_values),
    })


# =========================
# 👷 WORKER DASHBOARD
# =========================

@login_required
def worker_dashboard(request):
    user = request.user

    assigned_reports = WasteReport.objects.filter(
        assigned_worker=user,
        status="assigned"
    ).order_by("-created_at")

    assigned_tasks = assigned_reports.count()

    completed_tasks = WasteReport.objects.filter(
        assigned_worker=user,
        status="resolved"
    ).count()

    return render(request, "dashboards/worker_dashboard.html", {
        "assigned_tasks": assigned_tasks,
        "pending_tasks": assigned_tasks,  # same as assigned for now
        "completed_tasks": completed_tasks,
        "assigned_reports": assigned_reports,
    })


# =========================
# 🔐 AUTH
# =========================

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'accounts/login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.method == 'POST':
        form = CitizenRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/dashboard/')
    else:
        form = CitizenRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/login/')


@login_required
def become_worker(request):
    if request.method == 'POST':
        request.user.role = 'worker'
        request.user.save()
        return redirect('worker_dashboard')
    
    # Optional: If accessed via GET (though button should be POST), redirect back
    return redirect('citizen_dashboard')

