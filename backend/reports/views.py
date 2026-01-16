from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model

from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth
from django.utils.timezone import localdate
from datetime import timedelta
import json

from .models import WasteReport, SupportTicket
from .forms import WasteReportForm, WasteReportEditForm, SupportTicketForm
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, fields, Q
from notifications.models import Notification
from .utils import send_realtime_notification
import random

User = get_user_model()

# =====================================================
# 📊 ADMIN — ANALYTICS
# =====================================================
@login_required
def admin_analytics(request):
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "admin"):
        return render(request, "403.html")

    total_reports = WasteReport.objects.count()
    pending_count = WasteReport.objects.filter(status='pending').count()
    resolved_count = WasteReport.objects.filter(status='resolved').count()
    efficiency_rate = (resolved_count / total_reports * 100) if total_reports > 0 else 0

    status_counts = list(
        WasteReport.objects.values("status").annotate(count=Count("id"))
    )
    severity_counts = list(
        WasteReport.objects.values("severity").annotate(count=Count("id"))
    )
    waste_type_counts = list(
        WasteReport.objects.values("waste_type").annotate(count=Count("id"))
    )

    start_date = localdate() - timedelta(days=6)

    daily_reports = list(
        WasteReport.objects
        .filter(created_at__date__gte=start_date)
        .annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    monthly_qs = (
        WasteReport.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    monthly_reports = [
        {"label": m["month"].strftime("%b %Y"), "count": m["count"]}
        for m in monthly_qs
    ]

    return render(request, "dashboards/admin_analytics.html", {
        "total_reports": total_reports,
        "pending_count": pending_count,
        "resolved_count": resolved_count,
        "efficiency_rate": f"{efficiency_rate:.1f}%",
        "status_counts": json.dumps(status_counts),
        "severity_counts": json.dumps(severity_counts),
        "waste_type_counts": json.dumps(waste_type_counts),
        "daily_reports": json.dumps(daily_reports, default=str),
        "monthly_reports": json.dumps(monthly_reports),
    })

# =====================================================
# 📸 REPORT WASTE
# =====================================================
@login_required
def report_waste(request):
    if request.method == "POST":
        form = WasteReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.citizen = request.user
            report.save()
            return redirect("/dashboard/citizen/")
        return render(request, "reports/report_waste.html", {"form": form})

    return render(request, "reports/report_waste.html", {
        "form": WasteReportForm()
    })

# =====================================================
# 📄 MY REPORTS
# =====================================================
@login_required
def my_reports(request):
    from django.core.paginator import Paginator
    
    reports_list = WasteReport.objects.filter(
        citizen=request.user
    ).order_by("-created_at")
    
    # Paginate: 20 reports per page
    paginator = Paginator(reports_list, 20)
    page_number = request.GET.get('page', 1)
    reports = paginator.get_page(page_number)

    return render(request, "reports/my_reports.html", {"reports": reports})

# =====================================================
# 🔍 REPORT DETAIL
# =====================================================
@login_required
def report_detail(request, pk):
    # Allow access if:
    # 1. User is an Admin
    # 2. User is the Citizen who reported it
    # 3. User is the Worker assigned to it
    
    report = get_object_or_404(WasteReport, pk=pk)
    
    is_admin = getattr(request.user, "role", None) == "admin"
    is_citizen = report.citizen == request.user
    is_worker = report.assigned_worker == request.user
    
    if not (is_admin or is_citizen or is_worker):
        # If no access, throw 404 to hide existence or 403 for forbidden
        # Returning render with 403 is often cleaner for UX
        return render(request, "403.html", status=403)

    return render(request, "reports/report_detail.html", {"report": report})

# =====================================================
# 👷 WORKER — ASSIGNED REPORTS
# =====================================================
@login_required
def worker_assigned_reports(request):
    reports = WasteReport.objects.filter(
        assigned_worker=request.user,
        status="assigned"
    ).order_by("-created_at")

    return render(request, "reports/worker_assigned_reports.html", {"reports": reports})

# =====================================================
@login_required
def resolve_report(request, report_id):
    if request.method == "POST":
        report = get_object_or_404(
            WasteReport,
            id=report_id,
            assigned_worker=request.user,
            status="assigned"
        )
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        report.verification_otp = otp
        report.save()

        # Notify Citizen
        send_realtime_notification(
            user=report.citizen,
            title="Cleanup Verification OTP",
            message=f"The worker has completed the cleanup for your report. Please share this OTP with them to verify: {otp}",
            level="success"
        )
        
        # Add a success message or flag to the session to show OTP input on the dashboard
        request.session[f'verifying_report_{report_id}'] = True
        return redirect(f"/dashboard/worker/?verify={report_id}")
    
    return redirect("/reports/assigned/")

@login_required
def verify_otp(request, report_id):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        report = get_object_or_404(
            WasteReport,
            id=report_id,
            assigned_worker=request.user,
            status="assigned"
        )

        if report.verification_otp == otp_input:
            report.status = "resolved"
            report.resolved_at = timezone.now()
            report.verification_otp = None # Clear OTP after use
            report.save()
            
            # Final notification to citizen
            send_realtime_notification(
                user=report.citizen,
                title="Cleanup Confirmed! 🎉",
                message=f"Your waste report #{report.id} has been verified and successfully cleaned up.",
                level="success"
            )
            
            if f'verifying_report_{report_id}' in request.session:
                del request.session[f'verifying_report_{report_id}']
                
            return redirect("/dashboard/worker/")
        else:
            # Handle incorrect OTP (maybe add a flash message)
            return redirect(f"/dashboard/worker/?verify={report_id}&error=1")
            
    return redirect("/dashboard/worker/")

# =====================================================
# 🛠️ ADMIN — ALL REPORTS
# =====================================================
@login_required
def admin_all_reports(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    if getattr(request.user, "role", None) != "admin":
        return redirect("/dashboard/citizen/")

    # Start with all reports
    reports = WasteReport.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        reports = reports.filter(
            Q(location__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(citizen__username__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Waste type filter
    waste_type_filter = request.GET.get('waste_type', '')
    if waste_type_filter:
        reports = reports.filter(waste_type=waste_type_filter)
    
    # Severity filter
    severity_filter = request.GET.get('severity', '')
    if severity_filter:
        reports = reports.filter(severity=severity_filter)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            reports = reports.filter(created_at__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add 1 day to include the entire end date
            date_to_obj = date_to_obj + timedelta(days=1)
            reports = reports.filter(created_at__lt=date_to_obj)
        except ValueError:
            pass
    
    # Quick date filters
    quick_filter = request.GET.get('quick_filter', '')
    if quick_filter == 'today':
        reports = reports.filter(created_at__date=datetime.now().date())
    elif quick_filter == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        reports = reports.filter(created_at__gte=week_ago)
    elif quick_filter == 'month':
        month_ago = datetime.now() - timedelta(days=30)
        reports = reports.filter(created_at__gte=month_ago)
    
    # Order by latest first
    reports = reports.order_by("-created_at")
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page', 1)
    reports_page = paginator.get_page(page_number)
    
    workers = User.objects.filter(role="worker")

    # Handle POST for assignment
    if request.method == "POST":
        report = get_object_or_404(WasteReport, id=request.POST.get("report_id"))
        worker = get_object_or_404(User, id=request.POST.get("worker_id"))
        report.assigned_worker = worker
        report.status = "assigned"
        report.save()

        # Notify Worker
        send_realtime_notification(
            user=worker,
            title="New Job Assigned 🚛",
            message=f"You have been assigned to clean up Waste Report #{report.id} ({report.get_waste_type_display()}).",
            level="info"
        )
        return redirect("/reports/admin/")

    return render(request, "dashboards/admin_reports.html", {
        "reports": reports_page,
        "workers": workers,
        "search_query": search_query,
        "status_filter": status_filter,
        "waste_type_filter": waste_type_filter,
        "severity_filter": severity_filter,
        "date_from": date_from,
        "date_to": date_to,
        "quick_filter": quick_filter,
    })

# =====================================================
# 🗺️ MAP VIEW (FILTERABLE)
# =====================================================
@login_required
def waste_map_view(request):
    # 1. Role Restriction
    if getattr(request.user, "role", "citizen") == "citizen":
        reports = WasteReport.objects.filter(citizen=request.user)
    else:
        # Admin / Worker see all
        reports = WasteReport.objects.all()

    # 2. Filters
    severity = request.GET.get("severity")
    status = request.GET.get("status")
    waste_type = request.GET.get("waste_type")
    days = request.GET.get("days")  # time filter

    if severity:
        reports = reports.filter(severity=severity)
    if status:
        reports = reports.filter(status=status)
    if waste_type:
        reports = reports.filter(waste_type=waste_type)
    
    if days:
        try:
            d = int(days)
            start_date = timezone.now() - timedelta(days=d)
            reports = reports.filter(created_at__gte=start_date)
        except ValueError:
            pass

    data = []
    for r in reports:
        if r.latitude and r.longitude:
            data.append({
                "id": r.id,
                "lat": float(r.latitude),
                "lng": float(r.longitude),
                "waste_type": r.get_waste_type_display(),
                "severity": r.get_severity_display(),
                "status": r.status,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "image": r.image.url if r.image else "",
                "detail_url": f"/reports/detail/{r.id}/"
            })

    return render(request, "dashboards/map_view.html", {"reports": data})

@login_required
def delete_report(request, pk):
    report = get_object_or_404(
        WasteReport,
        pk=pk,
        citizen=request.user
    )

    # Optional safety: prevent deleting resolved reports
    if report.status != "pending":
        return redirect("/reports/my-reports/")

    if request.method == "POST":
        report.delete()
        return redirect("/reports/my-reports/")

    return render(request, "reports/confirm_delete.html", {
        "report": report
    })
@login_required
def admin_delete_report(request, pk):
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "admin"):
        return redirect("/dashboard/citizen/")

    report = get_object_or_404(WasteReport, pk=pk)

    if request.method == "POST":
        report.delete()
        return redirect("/reports/admin/")

    return render(request, "reports/admin_confirm_delete.html", {
        "report": report
    })


@login_required
def edit_report(request, pk):
    report = get_object_or_404(
        WasteReport,
        pk=pk,
        citizen=request.user
    )

    # Safety: do not allow editing resolved reports
    if report.status != "pending":
        return redirect("/reports/my-reports/")

    if request.method == "POST":
        form = WasteReportEditForm(
            request.POST,
            request.FILES,
            instance=report
        )
        if form.is_valid():
            form.save()
            return redirect(f"/reports/detail/{report.id}/")
    else:
        form = WasteReportEditForm(instance=report)

    return render(request, "reports/edit_report.html", {
        "form": form,
        "report": report
    })


@login_required
def worker_performance_dashboard(request):
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "admin"):
        return render(request, "403.html")

    workers = User.objects.filter(role="worker").annotate(
        total_assigned=Count("assigned_reports"),
        resolved_count=Count("assigned_reports", filter=Q(assigned_reports__status="resolved")),
        pending_count=Count("assigned_reports", filter=Q(assigned_reports__status__in=["pending", "assigned"])),
        avg_resolution_time=Avg(
            ExpressionWrapper(
                F("assigned_reports__resolved_at") - F("assigned_reports__created_at"),
                output_field=fields.DurationField()
            ),
            filter=Q(assigned_reports__status="resolved")
        )
    ).order_by("-resolved_count")

    # Helper to format duration
    worker_list = []
    for w in workers:
        td = w.avg_resolution_time
        if td:
            total_seconds = int(td.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            
            parts = []
            if days > 0: parts.append(f"{days}d")
            if hours > 0: parts.append(f"{hours}h")
            if minutes > 0: parts.append(f"{minutes}m")
            w.avg_resolution_time_formatted = " ".join(parts)
        else:
            w.avg_resolution_time_formatted = None
        worker_list.append(w)

    return render(request, "dashboards/worker_performance.html", {
        "workers": worker_list
    })
@login_required
def track_worker(request, report_id):
    report = get_object_or_404(
        WasteReport,
        id=report_id,
        citizen=request.user,
        status="assigned"
    )
    if not report.assigned_worker:
        return redirect("my_reports")
        
    return render(request, "reports/track_worker.html", {
        "report": report,
        "worker": report.assigned_worker
    })

@login_required
def rate_report(request, report_id):
    if request.method == "POST":
        report = get_object_or_404(
            WasteReport,
            id=report_id,
            citizen=request.user,
            status="resolved"
        )
        
        rating = request.POST.get("rating")
        review_text = request.POST.get("review_text", "")
        
        if rating and rating.isdigit():
            rating_val = int(rating)
            report.rating = rating_val
            report.review_text = review_text
            report.save()
            
            # Update Worker Performance
            worker = report.assigned_worker
            if worker:
                # Calculate new average
                stats = WasteReport.objects.filter(assigned_worker=worker, rating__isnull=False).aggregate(
                    avg_rating=Avg('rating'),
                    count=Count('id')
                )
                worker.average_rating = stats['avg_rating'] or 0.0
                worker.total_ratings = stats['count'] or 0
                worker.save()

                send_realtime_notification(
                    user=worker,
                    title="New Review Received! ⭐",
                    message=f"A citizen rated your cleanup for Report #{report.id} as {rating_val}/5 stars.",
                    level="success"
                )
                
        return redirect("/dashboard/citizen/")
    
    return redirect("/dashboard/citizen/")


# =====================================================
# 🛠️ SUPPORT TICKETS (Report a Problem)
# =====================================================
@login_required
def report_problem(request):
    """View for citizens to report general system issues"""
    if request.method == "POST":
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            return render(request, "reports/report_problem.html", {
                "success": True,
                "form": SupportTicketForm()
            })
    else:
        form = SupportTicketForm()
    
    return render(request, "reports/report_problem.html", {"form": form})


@login_required
def admin_support_tickets(request):
    """Admin view to see all support tickets"""
    if getattr(request.user, "role", None) != "admin":
        return redirect("/dashboard/citizen/")
    
    tickets = SupportTicket.objects.all().order_by("-created_at")
    return render(request, "reports/admin_support_tickets.html", {"tickets": tickets})


@login_required
def resolve_ticket(request, ticket_id):
    """Toggle resolution status of a support ticket"""
    if getattr(request.user, "role", None) != "admin":
        return redirect("/dashboard/citizen/")
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    ticket.is_resolved = not ticket.is_resolved
    ticket.save()
    return redirect("admin_support_tickets")
