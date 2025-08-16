import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import User, Place, Queue, Ticket, TicketStatus


@pytest.mark.django_db
def test_analytics_view():
    client = APIClient()

    admin = User.objects.create_user(username="admin", password="pass123", role="super_admin")
    client.force_authenticate(user=admin)   # 🔑 اینجا بجای force_login

    place = Place.objects.create(owner=admin, name="Test", latitude=0, longitude=0)
    queue = Queue.objects.create(place=place, name="Main")

    Ticket.objects.create(
        queue=queue,
        user=admin,
        number=1,
        status=TicketStatus.USED,
        created_at=timezone.now() - timezone.timedelta(minutes=10),
        called_at=timezone.now() - timezone.timedelta(minutes=5),
    )
    Ticket.objects.create(
        queue=queue,
        user=admin,
        number=2,
        status=TicketStatus.CANCELED,
    )

    response = client.get(f"/api/analytics/?place_id={place.id}")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["total_customers"] == 2
    assert "timeline" in data
