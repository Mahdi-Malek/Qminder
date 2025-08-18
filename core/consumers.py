import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs 
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings


User = get_user_model()


class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        User = self.scope["user"].__class__
        self.place_id = self.scope['url_route']['kwargs']['place_id']
        self.group_name = f"place_{self.place_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        در این نسخه پیام دلخواه از سمت کلاینت پردازش نمی‌شود.
        اگر در آینده لازم شد که کلاینت درخواست‌هایی بفرستد،
        اینجا با sync_to_async ایمن‌سازی ORM انجام شود.
        """
        pass

    async def queue_update(self, event):
        """
        دریافت آپدیت صف از group_send و ارسال آن به کلاینت.
        """
        data = event.get("data")
        await self.send(text_data=json.dumps(data, ensure_ascii=False))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.close(code=4001)  # No token provided
            return

        try:
            # استفاده از SimpleJWT برای اعتبارسنجی توکن
            access = AccessToken(token)
            user_id = access["user_id"]

            # واکشی یوزر از دیتابیس
            self.user = await sync_to_async(User.objects.get)(id=user_id)

            # ساختن group مخصوص این یوزر
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

        except Exception as e:
            await self.close(code=4003)  # Invalid token or other error

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["message"]))

