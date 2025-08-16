import pytest
from django.utils import timezone
from core.models import User, UserRoles, Place, Queue, Ticket, TicketStatus, Notification


@pytest.mark.django_db
def test_user_roles():
    user = User.objects.create(username="admin", role=UserRoles.SUPER_ADMIN)
    assert user.is_system_admin
    assert not user.is_place_admin
    assert not user.is_customer


@pytest.mark.django_db
def test_queue_statistics_update():
    admin = User.objects.create(username="placeadmin", role=UserRoles.PLACE_ADMIN)
    place = Place.objects.create(owner=admin, name="Test Place", latitude=0, longitude=0)
    queue = Queue.objects.create(place=place, name="Main Queue")

    user = User.objects.create(username="customer1", role=UserRoles.CUSTOMER)

    created1 = timezone.now() - timezone.timedelta(minutes=5)
    called1 = created1 + timezone.timedelta(minutes=3)  # اختلاف 3 دقیقه
    print(created1, called1)


    created2 = timezone.now() - timezone.timedelta(minutes=10)
    called2 = created2 + timezone.timedelta(minutes=4)  # اختلاف 4 دقیقه
    print(created2, called2)


    t1 = Ticket.objects.create(queue=queue, user=user, number=1, status=TicketStatus.USED)
    Ticket.objects.filter(pk=t1.pk).update(created_at=created1, called_at=called1)

    t2 = Ticket.objects.create(queue=queue, user=user, number=2, status=TicketStatus.USED)
    Ticket.objects.filter(pk=t2.pk).update(created_at=created2, called_at=called2)


    queue.update_statistics()

    assert queue.processed_count == 2
    assert queue.average_wait_time is not None
    assert queue.average_wait_time.total_seconds() > 0


@pytest.mark.django_db
def test_ticket_methods():
    admin = User.objects.create(username="placeadmin", role=UserRoles.PLACE_ADMIN)
    place = Place.objects.create(owner=admin, name="Test Place", latitude=0, longitude=0)
    queue = Queue.objects.create(place=place)

    user = User.objects.create(username="customer1", role=UserRoles.CUSTOMER)
    ticket = Ticket.objects.create(queue=queue, user=user, number=1)

    ticket.call()
    assert ticket.called_at is not None
    assert ticket.status == TicketStatus.ACTIVE  # call فقط زمان رو ست میکنه

    ticket.complete()
    assert ticket.status == TicketStatus.USED
    assert ticket.completed_at is not None

    ticket.requeue()
    assert ticket.status == TicketStatus.ACTIVE
    assert ticket.called_at is None

    ticket.cancel("No show")
    assert ticket.status == TicketStatus.CANCELED
    assert ticket.cancel_reason == "No show"


@pytest.mark.django_db
def test_notification_creation():
    user = User.objects.create(username="testuser")
    notif = Notification.objects.create(
        user=user,
        title="Test Notification",
        message="Hello!",
        channel="websocket",
        extra_data={"ticket_id": 1}
    )

    assert notif.extra_data["ticket_id"] == 1
    assert notif.is_read is False


