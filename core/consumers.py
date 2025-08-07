import json
from channels.generic.websocket import AsyncWebsocketConsumer

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.place_id = self.scope['url_route']['kwargs']['place_id']
        self.room_group_name = f'place_{self.place_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket (اختیاری)
    async def receive(self, text_data):
        data = json.loads(text_data)
        # در این نسخه، فقط سمت سرور پیام ارسال می‌کنه

    # دریافت پیام از سرور
    async def queue_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
