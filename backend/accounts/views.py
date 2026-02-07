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
    try:
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

        notifications = []
        try:
            notifications = user.notifications.filter(is_read=False)[:5]
        except Exception as e:
            print(f"Notification Fetch Error: {e}")

        return render(request, "dashboards/citizen_dashboard.html", {
            "total_reports": total_reports,
            "pending_reports": pending_reports,
            "resolved_reports": resolved_reports,
            "assigned_reports": assigned_reports,
            "recent_reports": recent_reports,
            "notifications": notifications,
            "verifying_reports": verifying_reports,
            "unrated_reports": unrated_reports,
        })
    except Exception as e:
        import traceback
        return HttpResponse(f"<h1>Dashboard Crash</h1><pre>{str(e)}\n{traceback.format_exc()}</pre>", status=500)


# =========================
# 🛠️ ADMIN DASHBOARD
# =========================

@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("citizen_dashboard")

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
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not identifier or not password:
            return render(request, 'accounts/login.html', {
                'error': 'Please provide both username/email and password'
            })

        # Try authenticating with identifier as username first
        user = authenticate(request, username=identifier, password=password)

        # If that fails, try looking up by email (case-insensitive)
        if not user:
            # Check if identifier looks like an email or matches any user's email field
            try:
                # Use iexact for case-insensitive email matching
                user_obj = User.objects.filter(email__iexact=identifier).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            except Exception:
                pass

        if user:
            if user.is_active:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'accounts/login.html', {
                    'error': 'This account is inactive.'
                })
        else:
            return render(request, 'accounts/login.html', {
                'error': 'Invalid email/username or password'
            })

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.method == 'POST':
        form = CitizenRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CitizenRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_profile(request):
    # Reload user from DB to ensure fresh data (e.g. recent shell updates)
    user = User.objects.get(pk=request.user.pk)

    if request.method == "POST":
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
            user.save()
        return redirect('user_profile')

    context = {}

    if user.role == "citizen":
        context["total_filed"] = WasteReport.objects.filter(citizen=user).count()
    
    elif user.role == "worker":
        context["completed_tasks"] = WasteReport.objects.filter(
            assigned_worker=user, 
            status="resolved"
        ).count()
    
    # Explicitly pass details to ensure availability
    context["user_email"] = user.email
    context["user_phone"] = user.phone

    return render(request, 'accounts/profile.html', context)


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        logout(request)
        return redirect('login')
    return redirect('user_profile')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def become_worker(request):
    if request.method == 'POST':
        request.user.role = 'worker'
        request.user.save()
        return redirect('worker_dashboard')
    
    # Optional: If accessed via GET (though button should be POST), redirect back
    return redirect('citizen_dashboard')


@login_required
def toggle_dark_mode(request):
    """Toggle dark mode preference and save to database"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        # Toggle the current state
        request.user.dark_mode = not request.user.dark_mode
        request.user.save()
        
        return JsonResponse({
            'success': True,
            'dark_mode': request.user.dark_mode
        })
    
    return JsonResponse({'success': False}, status=400)
