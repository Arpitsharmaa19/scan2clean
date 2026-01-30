from django.db import models
from django.conf import settings


class WasteReport(models.Model):

    # ====================
    # CHOICES
    # ====================
    WASTE_TYPE_CHOICES = [
        ('plastic', 'Plastic'),
        ('organic', 'Organic'),
        ('metal', 'Metal'),
        ('glass', 'Glass'),
        ('paper', 'Paper'),
        ('electronic', 'Electronic'),
        ('construction', 'Construction'),
        ('ewaste', 'E-Waste'),
        ('hazardous', 'Hazardous'),
        ('other', 'Other'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('resolved', 'Resolved'),
    ]

    # ====================
    # RELATIONSHIPS
    # ====================
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='waste_reports'
    )

    assigned_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reports'
    )

    # ====================
    # REPORT DETAILS
    # ====================
    image = models.ImageField(upload_to='waste_images/', null=True, blank=True)
    description = models.TextField(blank=True, default='')

    waste_type = models.CharField(
        max_length=20,
        choices=WASTE_TYPE_CHOICES,
        default='other'
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium'
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    location_source = models.CharField(
        max_length=20,
        choices=[
            ('auto', 'Auto-detected'),
            ('manual', 'Manually Selected'),
            ('gps-high-accuracy', 'High Accuracy GPS'),
            ('gps-low-accuracy', 'Low Accuracy GPS'),
        ],
        default='auto'
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    verification_otp = models.CharField(max_length=6, null=True, blank=True)

    # Citizen Feedback
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return (
            f"Report #{self.id} | "
            f"{self.waste_type} | "
            f"{self.severity} | "
            f"{self.status}"
        )


class SupportTicket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket from {self.user.username}: {self.subject}"
