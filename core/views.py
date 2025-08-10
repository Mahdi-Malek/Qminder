from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Max
from django.utils.dateparse import parse_datetime
from .models import Place, Queue, Ticket, Notification
from .serializers import (
    PlaceSerializer, QueueSerializer, QueueCreateSerializer,
    TicketSerializer, RegisterSerializer, NotificationSerializer
)
from .permissions import IsPlaceAdmin, IsSystemAdmin, IsQueueOwnerAdmin
from .utils import create_notification, send_ws_notification, send_email_notification, send_queue_update
from math import radians, cos, sin, asin, sqrt


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class NearbyPlacesView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            lat = float(request.GET.get("lat"))
            lon = float(request.GET.get("lon"))
            radius = float(request.GET.get("radius", 5))
        except (TypeError, ValueError):
            return Response({"detail": "invalid coordinates"}, status=400)
        q = Place.objects.all()
        nearby = [p for p in q if haversine(lat, lon, p.latitude, p.longitude) <= radius]
        serializer = PlaceSerializer(nearby, many=True, context={"request": request})
        return Response(serializer.data)


class PlaceViewSet(viewsets.ModelViewSet):
    serializer_class = PlaceSerializer
    permission_classes = [IsAuthenticated, IsPlaceAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return Place.objects.all()
        return Place.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class QueueAdminViewSet(viewsets.ModelViewSet):
    serializer_class = QueueSerializer
    permission_classes = [IsPlaceAdmin]

    def get_queryset(self):
        user = self.request.user
        return Queue.objects.filter(place__owner=user)

    def create(self, request, *args, **kwargs):
        serializer = QueueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queue = serializer.save()
        return Response(QueueSerializer(queue).data, status=201)

    @staticmethod
    def toggle_open(queue):
        queue.is_open = not queue.is_open
        queue.save()
        # notify active tickets
        title = "تغییر وضعیت صف"
        message = f"صف {queue.name} اکنون {'باز' if queue.is_open else 'بسته'} است."
        for t in queue.tickets.filter(status="active"):
            create_notification(t.user, title, message)
            send_ws_notification(t.user.id, {"title": title, "message": message})
            if t.user.email:
                send_email_notification(title, message, [t.user.email])
        send_queue_update(queue.place.id, {"type": "queue_status", "is_open": queue.is_open})
        return queue

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class JoinQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, place_id):
        user = request.user
        place = get_object_or_404(Place, id=place_id)
        try:
            queue = Queue.objects.filter(place=place, is_open=True).latest("created_at")
        except Queue.DoesNotExist:
            return Response({"detail": "no open queue"}, status=400)

        if Ticket.objects.filter(queue=queue, user=user, status="active").exists():
            return Response({"detail": "already active ticket"}, status=400)

        last_num = Ticket.objects.filter(queue=queue).aggregate(Max("number"))["number__max"] or 0
        ticket = Ticket.objects.create(queue=queue, user=user, number=last_num + 1)

        title = "نوبت ثبت شد"
        message = f"نوبت شما #{ticket.number}"
        create_notification(user, title, message)
        send_ws_notification(user.id, {"type": "ticket_created", "ticket": TicketSerializer(ticket).data})
        if user.email:
            send_email_notification(title, message, [user.email])
        send_queue_update(queue.place.id, {"type": "ticket_created", "ticket": TicketSerializer(ticket).data})
        return Response(TicketSerializer(ticket).data, status=201)


class LeaveQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
        ticket.cancel(reason="user_left" if not ticket.cancel_reason else ticket.cancel_reason) if ticket.status != "canceled" else None
        ticket.status = "canceled"
        ticket.save()

        title = "نوبت لغو شد"
        message = f"نوبت #{ticket.number} لغو شد"
        create_notification(request.user, title, message)
        send_ws_notification(request.user.id, {"type": "ticket_left", "ticket_id": ticket.id})
        if request.user.email:
            send_email_notification(title, message, [request.user.email])
        send_queue_update(ticket.queue.place.id, {"type": "ticket_left", "ticket_id": ticket.id})
        return Response({"status": "left"})


class AdminTicketsView(viewsets.ViewSet):
    permission_classes = [IsPlaceAdmin]

    def list(self, request, queue_id=None):
        queue = get_object_or_404(Queue, id=queue_id, place__owner=request.user)
        tickets = Ticket.objects.filter(queue=queue).order_by("number")
        return Response(TicketSerializer(tickets, many=True).data)

    def partial_update(self, request, queue_id=None):
        # expects ticket_id and action
        ticket_id = request.data.get("ticket_id")
        action = request.data.get("action")  # call/requeue/cancel
        ticket = get_object_or_404(Ticket, id=ticket_id, queue__id=queue_id, queue__place__owner=request.user)

        if action == "call":
            ticket.call()
            msg = f"نوبت #{ticket.number} فراخوانی شد"
            create_notification(ticket.user, "فراخوانی نوبت", msg)
            send_ws_notification(ticket.user.id, {"type": "ticket_called", "ticket": TicketSerializer(ticket).data})
            if ticket.user.email:
                send_email_notification("فراخوانی نوبت", msg, [ticket.user.email])
            send_queue_update(ticket.queue.place.id, {"type": "ticket_called", "ticket": TicketSerializer(ticket).data})
        elif action == "requeue":
            ticket.requeue()
            msg = f"نوبت #{ticket.number} بازگشت به صف"
            create_notification(ticket.user, "بازگشت نوبت", msg)
            send_ws_notification(ticket.user.id, {"type": "ticket_requeued", "ticket": TicketSerializer(ticket).data})
            send_queue_update(ticket.queue.place.id, {"type": "ticket_requeued", "ticket": TicketSerializer(ticket).data})
        elif action == "cancel":
            reason = request.data.get("reason")
            ticket.cancel(reason=reason)
            msg = f"نوبت #{ticket.number} کنسل شد"
            create_notification(ticket.user, "لغو نوبت", msg)
            send_ws_notification(ticket.user.id, {"type": "ticket_canceled", "ticket": TicketSerializer(ticket).data})
            if ticket.user.email:
                send_email_notification("لغو نوبت", msg, [ticket.user.email])
            send_queue_update(ticket.queue.place.id, {"type": "ticket_canceled", "ticket": TicketSerializer(ticket).data})
        else:
            return Response({"detail": "invalid action"}, status=400)

        # update queue statistics
        ticket.queue.update_statistics()
        return Response(TicketSerializer(ticket).data)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        return Response(NotificationSerializer(qs, many=True).data)


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return Response({"status": "read"})
