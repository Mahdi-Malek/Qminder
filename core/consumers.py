import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.place_id = self.scope['url_route']['kwargs']['place_id']
        self.group_name = f"place_{self.place_id}"

        # اضافه کردن به گروه
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
        user = self.scope.get("user")

        # اگر کاربر احراز هویت نشده باشد، اتصال قطع می‌شود
        if not user or not getattr(user, "is_authenticated", False):
            await self.close()
            return

        # در صورت نیاز: گرفتن دوباره کاربر از DB (ایمن برای async)
        self.user = await sync_to_async(User.objects.get)(id=user.id)

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        """
        ارسال اعلان به کلاینت.
        """
        message = event.get("message")
        if isinstance(message, dict):
            await self.send(text_data=json.dumps(message, ensure_ascii=False))
        else:
            await self.send(text_data=str(message))
