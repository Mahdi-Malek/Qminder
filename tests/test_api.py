import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from core.models import User, Place, Queue, Ticket

pytestmark = pytest.mark.django_db

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def customer():
    return User.objects.create_user(username="u", password="p", role="customer")

@pytest.fixture
def place_admin():
    return User.objects.create_user(username="admin", password="p", role="place_admin")

@pytest.fixture
def place(place_admin):
    return Place.objects.create(owner=place_admin, name="Shop", latitude=35.7, longitude=51.4, opening_time="09:00", closing_time="18:00")

@pytest.fixture
def queue(place):
    return Queue.objects.create(place=place, name="Main")

def test_register_and_login(client):
    url = reverse("register")
    resp = client.post(url, {"username": "bob", "password": "pass123", "role": "customer"})
    assert resp.status_code == 201

def test_join_leave_flow(client, customer, queue):
    client.force_authenticate(customer)
    join_url = reverse("join-queue", kwargs={"place_id": queue.place.id})
    r = client.post(join_url)
    assert r.status_code == 201
    ticket_id = r.json().get("id")
    leave_url = reverse("leave-queue", kwargs={"ticket_id": ticket_id})
    r2 = client.post(leave_url)
    assert r2.status_code == 200
