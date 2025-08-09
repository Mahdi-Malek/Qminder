from rest_framework import serializers
from .models import Place, Queue, Ticket, User
from django.contrib.auth import get_user_model

User = get_user_model()

class PlaceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            "id", "owner", "name", "description", "latitude", "longitude",
            "logo", "logo_url", "opening_time", "closing_time",
            "max_concurrent_queues", "ticket_interval_minutes",
            "created_at", "updated_at"
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def get_logo_url(self, obj):
        request = self.context.get("request")
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "phone"]

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            role=validated_data.get("role", "customer"),
            phone=validated_data.get("phone", ""),
        )
        user.set_password(validated_data["password"])
        if validated_data.get("role") == "place_admin":
            user.is_place_admin = True
        user.save()
        return user



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "first_name", "last_name"]
        read_only_fields = ["id", "username"]

class AdminUpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role"]

