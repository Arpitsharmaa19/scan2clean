from django.urls import path
from . import views
from . import export_views

urlpatterns = [
    # Citizen
    path("report/", views.report_waste, name="report_waste"),
    path("my-reports/", views.my_reports, name="my_reports"),
    path("detail/<int:pk>/", views.report_detail, name="report_detail"),
    path("rate/<int:report_id>/", views.rate_report, name="rate_report"),

    # Worker
    path("assigned/", views.worker_assigned_reports, name="worker_assigned_reports"),
    path("resolve/<int:report_id>/", views.resolve_report, name="resolve_report"),
    path("verify-otp/<int:report_id>/", views.verify_otp, name="verify_otp"),
    path("track/<int:report_id>/", views.track_worker, name="track_worker"),

    # Admin
    path("admin/", views.admin_all_reports, name="admin_all_reports"),
    path("admin/analytics/", views.admin_analytics, name="admin_analytics"),
    path("worker-performance/", views.worker_performance_dashboard, name="worker_performance_dashboard"),

    # Map
    path("map/", views.waste_map_view, name="waste_map"),
    path("delete/<int:pk>/", views.delete_report, name="delete_report"),
    path("edit/<int:pk>/", views.edit_report, name="edit_report"),
    path("admin/delete/<int:pk>/", views.admin_delete_report, name="admin_delete_report"),

    # Export (Admin only)
    path("export/csv/", export_views.export_reports_csv, name="export_reports_csv"),
    path("export/pdf/<int:report_id>/", export_views.export_report_pdf, name="export_report_pdf"),

    # Support Tickets
    path("report-problem/", views.report_problem, name="report_problem"),
    path("admin/tickets/", views.admin_support_tickets, name="admin_support_tickets"),
    path("admin/tickets/resolve/<int:ticket_id>/", views.resolve_ticket, name="resolve_ticket"),

]

