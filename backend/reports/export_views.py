import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import WasteReport


# =====================================================
# 📥 CSV EXPORT - All Reports
# =====================================================
@login_required
def export_reports_csv(request):
    """Export all waste reports as CSV file (Admin only)"""
    
    # Check admin permission
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "admin"):
        return render(request, "403.html")
    
    # Get all reports
    reports = WasteReport.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status = request.GET.get('status')
    severity = request.GET.get('severity')
    waste_type = request.GET.get('waste_type')
    
    if status:
        reports = reports.filter(status=status)
    if severity:
        reports = reports.filter(severity=severity)
    if waste_type:
        reports = reports.filter(waste_type=waste_type)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="waste_reports_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Report ID',
        'Reported By',
        'Email',
        'Waste Type',
        'Severity',
        'Status',
        'Description',
        'Latitude',
        'Longitude',
        'Created At',
        'Resolved At',
        'Assigned Worker',
        'Resolution Time (hours)'
    ])
    
    # Write data rows
    for report in reports:
        # Calculate resolution time
        resolution_time = ''
        if report.resolved_at and report.created_at:
            delta = report.resolved_at - report.created_at
            resolution_time = f"{delta.total_seconds() / 3600:.1f}"
        
        writer.writerow([
            report.id,
            report.citizen.username if report.citizen else 'N/A',
            report.citizen.email if report.citizen else 'N/A',
            report.get_waste_type_display(),
            report.get_severity_display(),
            report.status.capitalize(),
            report.description[:100] + ('...' if len(report.description) > 100 else ''),
            report.latitude or 'N/A',
            report.longitude or 'N/A',
            report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            report.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if report.resolved_at else 'N/A',
            report.assigned_worker.username if report.assigned_worker else 'Unassigned',
            resolution_time
        ])
    
    return response


# =====================================================
# 📄 PDF EXPORT - Single Report Card
# =====================================================
@login_required
def export_report_pdf(request, report_id):
    """Generate PDF report card for a single waste report"""
    
    report = get_object_or_404(WasteReport, id=report_id)
    
    # Check permission (citizen can only view their own reports, admin/worker can view all)
    user_role = getattr(request.user, "role", "citizen")
    if user_role == "citizen" and report.citizen != request.user:
        return render(request, "403.html")
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#16a34a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#15803d'),
        spaceAfter=6,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    
    # Title
    story.append(Paragraph("♻️ Scan2Clean Waste Report", title_style))
    story.append(Paragraph(f"Report #{report.id}", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))
    
    # Report Image (if exists)
    if report.image:
        try:
            img_path = report.image.path
            img = Image(img_path, width=4*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))
        except:
            pass
    
    # Report Details Table
    data = [
        ['Field', 'Value'],
        ['Waste Type', report.get_waste_type_display()],
        ['Severity Level', report.get_severity_display()],
        ['Status', report.status.capitalize()],
        ['Reported By', report.citizen.username if report.citizen else 'N/A'],
        ['Email', report.citizen.email if report.citizen else 'N/A'],
        ['Reported On', report.created_at.strftime('%B %d, %Y at %I:%M %p')],
    ]
    
    if report.assigned_worker:
        data.append(['Assigned Worker', report.assigned_worker.username])
    
    if report.resolved_at:
        data.append(['Resolved On', report.resolved_at.strftime('%B %d, %Y at %I:%M %p')])
        # Calculate resolution time
        delta = report.resolved_at - report.created_at
        hours = delta.total_seconds() / 3600
        data.append(['Resolution Time', f"{hours:.1f} hours"])
    
    if report.latitude and report.longitude:
        data.append(['Location', f"{report.latitude}, {report.longitude}"])
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f0fdf4')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Description
    story.append(Paragraph("Description", heading_style))
    story.append(Paragraph(report.description, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>Scan2Clean Waste Management System"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF from buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report.id}.pdf"'
    response.write(pdf)
    
    return response
