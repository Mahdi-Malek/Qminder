from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db.models import Max
from .models import Place, Queue, Ticket
from .serializers import PlaceSerializer, QueueSerializer, TicketSerializer, RegisterSerializer
from math import radians, cos, sin, asin, sqrt
from rest_framework.exceptions import ValidationError, NotAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from .utils import send_queue_update
from rest_framework import generics
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from .serializers import UserSerializer, AdminUpdateUserSerializer
from .permissions import IsSystemAdmin



User = get_user_model()



def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


class NearbyPlacesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
            max_distance = float(request.GET.get('radius', 5))
        except (TypeError, ValueError):
            raise ValidationError({"detail": "Invalid or missing coordinates."})

        all_places = Place.objects.all()
        nearby = [p for p in all_places if haversine(lat, lon, p.latitude, p.longitude) <= max_distance]
        serializer = PlaceSerializer(nearby, many=True)
        return Response(serializer.data)


class QueueStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, place_id):
        try:
            queue = Queue.objects.filter(place_id=place_id).latest('created_at')
        except Queue.DoesNotExist:
            return Response({'detail': 'Queue not found'}, status=status.HTTP_404_NOT_FOUND)

        tickets = Ticket.objects.filter(queue=queue, is_active=True).order_by('number')
        return Response({
            'queue': QueueSerializer(queue).data,
            'tickets': TicketSerializer(tickets, many=True).data
        })


class JoinQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, place_id):
        user = request.user
        try:
            queue = Queue.objects.filter(place_id=place_id, is_open=True).latest('created_at')
        except Queue.DoesNotExist:
            return Response({'detail': 'No open queue'}, status=status.HTTP_400_BAD_REQUEST)

        last_ticket_number = Ticket.objects.filter(queue=queue).aggregate(Max('number'))['number__max'] or 0

        # جلوگیری از گرفتن چند نوبت فعال توسط یک کاربر
        if Ticket.objects.filter(queue=queue, user=user, is_active=True).exists():
            return Response({'detail': 'You already have an active ticket.'}, status=status.HTTP_400_BAD_REQUEST)

        ticket = Ticket.objects.create(queue=queue, user=user, number=last_ticket_number + 1)
        send_queue_update(queue.place.id, {
                "type": "ticket_created",
                "ticket": TicketSerializer(ticket).data
            })
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)


class LeaveQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id, user=request.user)
        except Ticket.DoesNotExist:
            return Response({'detail': 'Ticket not found or unauthorized.'}, status=status.HTTP_404_NOT_FOUND)

        ticket.is_active = False
        ticket.save()
        send_queue_update(ticket.queue.place.id, {
                "type": "ticket_left",
                "ticket_id": ticket.id
            })
        return Response({'status': 'left'}, status=status.HTTP_200_OK)



class IsPlaceAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_place_admin


class AdminQueuesView(ListCreateAPIView):
    permission_classes = [IsPlaceAdmin]
    serializer_class = QueueSerializer

    def get_queryset(self):
        return Queue.objects.filter(place__owner=self.request.user)

    def perform_create(self, serializer):
        place_id = self.request.data.get("place_id")
        place = get_object_or_404(Place, id=place_id, owner=self.request.user)
        serializer.save(place=place)


class AdminTicketsView(APIView):
    permission_classes = [IsPlaceAdmin]

    def get(self, request, queue_id):
        queue = get_object_or_404(Queue, id=queue_id, place__owner=request.user)
        tickets = Ticket.objects.filter(queue=queue).order_by('number')
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, queue_id):
        queue = get_object_or_404(Queue, id=queue_id, place__owner=request.user)

        ticket_id = request.data.get("ticket_id")
        new_status = request.data.get("status")

        if new_status not in dict(Ticket.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        ticket = get_object_or_404(Ticket, id=ticket_id, queue=queue)
        ticket.status = new_status
        ticket.save()

        send_queue_update(queue.place.id, {
            "type": "ticket_status_changed",
            "ticket_id": ticket.id,
            "new_status": new_status
        })

        return Response(TicketSerializer(ticket).data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]



class IsPlaceOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_staff

class PlaceViewSet(viewsets.ModelViewSet):
    serializer_class = PlaceSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlaceOwner]

    def get_queryset(self):
        # مدیر سیستم همه مکان‌ها را می‌بیند
        if self.request.user.is_staff:
            return Place.objects.all()
        return Place.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)



class UserManagementViewSet(viewsets.ViewSet):
    permission_classes = [IsSystemAdmin]

    def list(self, request):
        """لیست همه کاربران"""
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """دریافت مشخصات یک کاربر"""
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def update_role(self, request, pk=None):
        """تغییر نقش کاربر"""
        user = get_object_or_404(User, pk=pk)
        serializer = AdminUpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Role updated successfully"})
