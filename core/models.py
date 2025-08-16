from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import JSONField


class UserRoles:
    CUSTOMER = "customer"
    PLACE_ADMIN = "place_admin"
    SUPER_ADMIN = "super_admin"

    CHOICES = (
        (CUSTOMER, "Customer"),
        (PLACE_ADMIN, "Place Admin"),
        (SUPER_ADMIN, "Super Admin"),
    )


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRoles.CHOICES, default=UserRoles.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True, null=True)

    @property
    def is_customer(self):
        return self.role == UserRoles.CUSTOMER

    @property
    def is_place_admin(self):
        return self.role == UserRoles.PLACE_ADMIN

    @property
    def is_system_admin(self):
        return self.role == UserRoles.SUPER_ADMIN

    def __str__(self):
        return self.username


class Place(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="places")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    logo = models.ImageField(upload_to="place_logos/", blank=True, null=True)

    opening_time = models.TimeField(default="09:00")
    closing_time = models.TimeField(default="18:00")
    max_concurrent_queues = models.PositiveIntegerField(default=1)
    ticket_interval_minutes = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class Queue(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="queues")
    name = models.CharField(max_length=255, default="Default")
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # statistics
    processed_count = models.PositiveIntegerField(default=0)
    total_tickets = models.PositiveIntegerField(default=0)
    last_ticket_number = models.PositiveIntegerField(default=0)
    average_wait_time = models.DurationField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def close(self):
        self.is_open = False
        self.closed_at = timezone.now()
        self.save()

    def open(self):
        self.is_open = True
        self.closed_at = None
        self.save()

    def update_statistics(self):
        tickets = self.tickets.filter(status=TicketStatus.USED)
        self.processed_count = tickets.count()

        wait_seconds = []
        for t in tickets:
            if t.called_at and t.created_at:
                diff = (t.called_at - t.created_at).total_seconds()
                print(t.called_at, t.created_at)
                print(diff)
                if diff > 0:  # فقط اختلاف مثبت
                    wait_seconds.append(diff)

        if wait_seconds:
            from datetime import timedelta
            avg_seconds = sum(wait_seconds) / len(wait_seconds)
            self.average_wait_time = timedelta(seconds=avg_seconds)
        else:
            self.average_wait_time = timezone.timedelta(seconds=0)

        self.save()




class TicketStatus:
    ACTIVE = "active"
    USED = "used"
    CANCELED = "canceled"

    CHOICES = (
        (ACTIVE, "Active"),
        (USED, "Used"),
        (CANCELED, "Canceled"),
    )


class Ticket(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=TicketStatus.CHOICES, default=TicketStatus.ACTIVE)
    cancel_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("queue", "number")
        ordering = ("number",)

    def call(self):
        self.called_at = timezone.now()
        self.save()

    def complete(self):
        self.status = TicketStatus.USED
        self.completed_at = timezone.now()
        self.save()

    def requeue(self):
        self.status = TicketStatus.ACTIVE
        self.called_at = None
        self.completed_at = None
        self.save()

    def cancel(self, reason=None):
        self.status = TicketStatus.CANCELED
        self.cancel_reason = reason
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Ticket #{self.number} ({self.queue})"
    
    @property
    def wait_time_seconds(self):
        if self.called_at and self.created_at:
            return (self.called_at - self.created_at).total_seconds()
        return None


class Notification(models.Model):
    CHANNEL_CHOICES = (
        ("websocket", "WebSocket"),
        ("email", "Email"),
        ("push", "Push"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="websocket")
    extra_data = JSONField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} - {self.title}"
