from rest_framework import serializers
from .models import Place, Queue, Ticket

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'

class QueueSerializer(serializers.ModelSerializer):
    place = PlaceSerializer()
    class Meta:
        model = Queue
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    queue = QueueSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
