from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_queue_update(place_id, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'place_{place_id}',
        {
            "type": "queue_update",
            "data": data
        }
    )
