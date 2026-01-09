from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model

from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth
from django.utils.timezone import localdate
from datetime import timedelta
import json

from .models import WasteReport
from .forms import WasteReportForm, WasteReportEditForm
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, fields, Q

User = get_user_model()

# =====================================================
# 📊 ADMIN — ANALYTICS
# =====================================================
@login_required
def admin_analytics(request):
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "admin"):
        return render(request, "403.html")

    total_reports = WasteReport.objects.count()

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
    reports = WasteReport.objects.filter(
        citizen=request.user
    ).order_by("-created_at")

    return render(request, "reports/my_reports.html", {"reports": reports})

# =====================================================
# 🔍 REPORT DETAIL
# =====================================================
@login_required
def report_detail(request, pk):
    report = get_object_or_404(
        WasteReport,
        pk=pk,
        citizen=request.user
    )
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
# ✅ WORKER — RESOLVE REPORT
# =====================================================
@login_required
def resolve_report(request, report_id):
    if request.method == "POST":
        report = get_object_or_404(
            WasteReport,
            id=report_id,
            assigned_worker=request.user
        )
        report.status = "resolved"
        report.resolved_at = timezone.now()
        report.save()
    
    return redirect("/reports/assigned/")

# =====================================================
# 🛠️ ADMIN — ALL REPORTS
# =====================================================
@login_required
def admin_all_reports(request):
    if getattr(request.user, "role", None) != "admin":
        return redirect("/dashboard/citizen/")

    reports = WasteReport.objects.all().order_by("-created_at")
    workers = User.objects.filter(role="worker")

    if request.method == "POST":
        report = get_object_or_404(WasteReport, id=request.POST.get("report_id"))
        worker = get_object_or_404(User, id=request.POST.get("worker_id"))
        report.assigned_worker = worker
        report.status = "assigned"
        report.save()
        return redirect("/reports/admin/")

    return render(request, "dashboards/admin_reports.html", {
        "reports": reports,
        "workers": workers
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
