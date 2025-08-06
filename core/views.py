from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db.models import Max
from .models import Place, Queue, Ticket
from .serializers import PlaceSerializer, QueueSerializer, TicketSerializer
from math import radians, cos, sin, asin, sqrt
from rest_framework.exceptions import ValidationError, NotAuthenticated


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
        return Response({'status': 'left'}, status=status.HTTP_200_OK)
