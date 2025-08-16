from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Place, Queue, Ticket, Notification

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role", "phone")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "phone", "first_name", "last_name")
        read_only_fields = ("id", "username")


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("role",)


class PlaceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            "id", "owner", "name", "description", "latitude", "longitude",
            "logo", "logo_url", "opening_time", "closing_time",
            "max_concurrent_queues", "ticket_interval_minutes",
            "created_at", "updated_at",
        )
        read_only_fields = ("owner", "created_at", "updated_at")

    def get_logo_url(self, obj):
        request = self.context.get("request")
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None


class QueueSerializer(serializers.ModelSerializer):
    place = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Queue
        fields = ("id", "place", "name", "is_open", "created_at", "closed_at",
                  "processed_count", "average_wait_time")


class QueueCreateSerializer(serializers.ModelSerializer):
    place_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Queue
        fields = ("id", "place_id", "name", "is_open")

    def create(self, validated_data):
        place_id = validated_data.pop("place_id")
        from .models import Place
        place = Place.objects.get(id=place_id)
        queue = Queue.objects.create(place=place, **validated_data)
        return queue


class TicketSerializer(serializers.ModelSerializer):
    queue = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Ticket
        fields = ("id", "queue", "user", "number", "status",
                  "cancel_reason", "created_at", "called_at", "completed_at")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "queue", "user", "number", "status",
                  "created_at", "called_at", "completed_at")
        read_only_fields = ("id", "user", "number", "status",
                            "created_at", "called_at", "completed_at")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        queue = validated_data["queue"]

        # آخرین شماره نوبت در این صف
        last_ticket = queue.tickets.order_by("-number").first()
        next_number = last_ticket.number + 1 if last_ticket else 1

        ticket = Ticket.objects.create(
            queue=queue,
            user=user,
            number=next_number,
            status=TicketStatus.ACTIVE,
        )
        return ticket



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "user", "title", "message", "channel", "is_read", "created_at")
        read_only_fields = ("id", "created_at", "user")
