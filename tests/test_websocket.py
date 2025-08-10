import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from core.asgi import application
from core.models import Place, Queue
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

User = get_user_model()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_ticket_created():
    # ایجاد یوزر
    user = await sync_to_async(User.objects.create_user)(
        username="admin",
        password="123456",
        role="place_admin"
    )

    # ایجاد مکان
    place = await sync_to_async(Place.objects.create)(
        owner=user,
        name="Test Place",
        description="test",
        latitude=0,
        longitude=0,
        opening_time="09:00",
        closing_time="18:00",
        max_concurrent_queues=1,
        ticket_interval_minutes=5
    )

    # ایجاد صف
    await sync_to_async(Queue.objects.create)(
        place=place,
        name="Test Queue",
        is_open=True
    )

    # اتصال WebSocket
    communicator = WebsocketCommunicator(application, f"/ws/queue/{place.id}/")
    connected, _ = await communicator.connect()
    assert connected

    # ارسال پیام به گروه
    channel_layer = get_channel_layer()
    data = {"type": "ticket_created", "ticket": {"id": 1, "number": 1}}

    await channel_layer.group_send(f"place_{place.id}", {
        "type": "queue_update",
        "data": data
    })

    # دریافت پیام
    response = await communicator.receive_json_from()
    assert response == data

    await communicator.disconnect()
