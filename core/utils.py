import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def send_queue_update(place_id: int, data: dict):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"place_{place_id}",
        {
            "type": "queue_update",
            "data": data
        }
    )

def create_notification(user, title: str, message: str, channel: str = "websocket"):
    try:
        Notification.objects.create(user=user, title=title, message=message, channel=channel)
    except Exception:
        # don't fail the request if notification cannot be saved
        pass

def send_ws_notification(user_id: int, data: dict):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_notification",
            "message": json.dumps(data, ensure_ascii=False)
        }
    )

def send_email_notification(subject: str, message: str, recipient_list: list):
    try:
        send_mail(subject, message, getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"), recipient_list, fail_silently=True)
    except Exception:
        pass


def send_queue_event(place_id, event_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"place_{place_id}",
        {
            "type": "queue_update",
            "data": {"type": event_type, "payload": data},
        }
    )

def send_user_notification(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_notification",
            "message": message,
        }
    )
