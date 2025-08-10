from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Place, Queue, Ticket, Notification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional", {"fields": ("role", "phone")}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "opening_time", "closing_time")
    search_fields = ("name", "owner__username")

@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ("name", "place", "is_open", "processed_count")
    list_filter = ("is_open",)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("number", "queue", "user", "status", "created_at")
    list_filter = ("status",)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "channel", "is_read", "created_at")
    list_filter = ("channel", "is_read")
