import pytest
from channels.testing import WebsocketCommunicator
from core.asgi import application
from core.models import Place, Queue
import json

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_ticket_created():
    place = Place.objects.create(name="Test Place", latitude=0, longitude=0)
    queue = Queue.objects.create(place=place, is_open=True)

    communicator = WebsocketCommunicator(application, f"/ws/queue/{place.id}/")
    connected, _ = await communicator.connect()
    assert connected

    # ارسال پیام از سمت سرور به این گروه
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()

    data = {
        "type": "ticket_created",
        "ticket": {"id": 1, "number": 1}
    }

    await channel_layer.group_send(f"place_{place.id}", {
        "type": "queue_update",
        "data": data
    })

    response = await communicator.receive_json_from()
    assert response == data

    await communicator.disconnect()
