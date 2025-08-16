from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Ticket
from .utils import send_queue_update

@receiver([post_save, post_delete], sender=Ticket)
def update_queue_stats(sender, instance, **kwargs):
    queue = instance.queue
    queue.update_statistics()
    send_queue_update(queue.place.id, {
        "type": "queue_update",
        "queue_id": queue.id,
        "stats": {
            "processed_count": queue.processed_count,
            "total_tickets": queue.total_tickets,
            "last_ticket_number": queue.last_ticket_number,
            "average_wait_time": queue.average_wait_time.total_seconds() if queue.average_wait_time else None
        }
    })
