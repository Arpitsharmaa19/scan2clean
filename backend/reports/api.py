from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import WasteReport, SupportTicket
from .serializers import WasteReportSerializer, SupportTicketSerializer
from .utils import send_realtime_notification
import random

class WasteReportViewSet(viewsets.ModelViewSet):
    queryset = WasteReport.objects.all()
    serializer_class = WasteReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            queryset = WasteReport.objects.all()
        elif user.role == 'worker':
            queryset = WasteReport.objects.filter(assigned_worker=user)
        else:
            queryset = WasteReport.objects.filter(citizen=user)

        # Filtering
        status_param = self.request.query_params.get('status')
        severity_param = self.request.query_params.get('severity')
        waste_type_param = self.request.query_params.get('waste_type')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if severity_param:
            queryset = queryset.filter(severity=severity_param)
        if waste_type_param:
            queryset = queryset.filter(waste_type=waste_type_param)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        report = self.get_object()
        if report.assigned_worker != request.user:
            return Response({'error': 'Not assigned to you'}, status=status.HTTP_403_FORBIDDEN)
        
        otp = str(random.randint(100000, 999999))
        report.verification_otp = otp
        report.save()

        send_realtime_notification(
            user=report.citizen,
            title="Cleanup Verification OTP",
            message=f"The worker has completed the cleanup for your report. Use OTP: {otp}",
            level="success"
        )
        return Response({'status': 'OTP generated', 'id': report.id})

    @action(detail=True, methods=['post'])
    def verify_otp(self, request, pk=None):
        report = self.get_object()
        otp_input = request.data.get('otp')
        
        if report.verification_otp == otp_input:
            report.status = "resolved"
            report.resolved_at = timezone.now()
            report.verification_otp = None
            report.save()
            
            send_realtime_notification(
                user=report.citizen,
                title="Cleanup Confirmed! 🎉",
                message=f"Your waste report #{report.id} has been verified.",
                level="success"
            )
            return Response({'status': 'verified'})
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        report = self.get_object()
        if report.citizen != request.user:
            return Response({'error': 'Only the creator can rate'}, status=status.HTTP_403_FORBIDDEN)
            
        rating = request.data.get('rating')
        review = request.data.get('review', '')
        
        if rating:
            rating_val = int(rating)
            report.rating = rating_val
            report.review_text = review
            report.save()

            # Update Worker Performance
            worker = report.assigned_worker
            if worker:
                from django.db.models import Avg, Count
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

            return Response({'status': 'rated'})
        return Response({'error': 'Rating required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def analytics(self, request):
        from django.db.models import Count
        from django.db.models.functions import TruncDay, TruncMonth
        from datetime import timedelta
        from django.utils.timezone import localdate

        total_reports = WasteReport.objects.count()
        status_counts = list(WasteReport.objects.values("status").annotate(count=Count("id")))
        severity_counts = list(WasteReport.objects.values("severity").annotate(count=Count("id")))
        waste_type_counts = list(WasteReport.objects.values("waste_type").annotate(count=Count("id")))

        start_date = localdate() - timedelta(days=6)
        daily_reports = list(
            WasteReport.objects
            .filter(created_at__date__gte=start_date)
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return Response({
            "total_reports": total_reports,
            "status_counts": status_counts,
            "severity_counts": severity_counts,
            "waste_type_counts": waste_type_counts,
            "daily_reports": daily_reports
        })

    @action(detail=False, methods=['get'])
    def optimized_route(self, request):
        from .utils import get_optimized_route, batch_reports_by_proximity
        
        user = request.user
        if user.role != 'worker':
            return Response({'error': 'Workers only'}, status=status.HTTP_403_FORBIDDEN)
            
        worker_lat = float(user.latitude) if user.latitude else None
        worker_lng = float(user.longitude) if user.longitude else None
        
        if not worker_lat or not worker_lng:
            return Response({
                'error': 'Worker location required',
                'message': 'Please turn on your online status to provide your current location'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        reports = WasteReport.objects.filter(assigned_worker=user, status='assigned')
        if not reports.exists():
            return Response({
                'status': 'no_jobs',
                'message': 'No assigned reports found',
                'batches': []
            })
            
        # Separate reports with and without location
        reports_with_location = []
        reports_without_location = []
        
        for r in reports:
            if r.latitude and r.longitude:
                reports_with_location.append({
                    'id': r.id,
                    'lat': float(r.latitude),
                    'lng': float(r.longitude),
                    'type': r.get_waste_type_display(),
                    'severity': r.severity,
                    'description': r.description[:50] + '...' if len(r.description) > 50 else r.description
                })
            else:
                reports_without_location.append({
                    'id': r.id,
                    'type': r.get_waste_type_display(),
                    'severity': r.severity,
                    'description': r.description[:50] + '...' if len(r.description) > 50 else r.description
                })
        
        # If no reports have location data
        if not reports_with_location:
            return Response({
                'error': 'no_location_data',
                'message': f'All {len(reports_without_location)} assigned report(s) are missing location data',
                'reports_without_location': reports_without_location,
                'suggestion': 'Please contact admin to update report locations'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Optimize route for reports with location
        optimized = get_optimized_route(worker_lat, worker_lng, reports_with_location)
        
        # Group into batches
        batches = batch_reports_by_proximity(optimized)
        
        response_data = {
            'worker_location': {'lat': worker_lat, 'lng': worker_lng},
            'batches': batches,
            'optimized_order': [r['id'] for r in optimized],
            'total_reports': len(reports),
            'routable_reports': len(reports_with_location)
        }
        
        # Include warning if some reports lack location
        if reports_without_location:
            response_data['warning'] = f'{len(reports_without_location)} report(s) excluded due to missing location'
            response_data['reports_without_location'] = reports_without_location
        
        return Response(response_data)

class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
