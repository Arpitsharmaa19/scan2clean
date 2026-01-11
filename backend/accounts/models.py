from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Real-time tracking
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    # Performance tracking
    average_rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.username} ({self.role})"
