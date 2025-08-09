from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("place_admin", "Place Admin"),
        ("super_admin", "Super Admin"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    phone = models.CharField(max_length=20, blank=True, null=True)

    def is_system_admin(self):
        return self.role == "super_admin"

    def is_place_admin(self):
        return self.role == "place_admin"

    def __str__(self):
        return self.username



class Place(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="places")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    logo = models.ImageField(upload_to="places/logos/", blank=True, null=True)

    # تنظیمات
    opening_time = models.TimeField(default="09:00")
    closing_time = models.TimeField(default="18:00")
    max_concurrent_queues = models.PositiveIntegerField(default=1)
    ticket_interval_minutes = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Queue(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='queues')
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('canceled', 'Canceled'),
    ]
    
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        return self.status == 'active'


    class Meta:
        unique_together = ('queue', 'number')



