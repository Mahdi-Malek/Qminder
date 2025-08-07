from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    is_client = models.BooleanField(default=False)
    is_place_admin = models.BooleanField(default=False)

class Place(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='places')

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