from rest_framework.permissions import BasePermission


class IsPlaceAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "role", "") == "place_admin")


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "role", "") == "super_admin")


class IsQueueOwnerAdmin(BasePermission):
    """
    Check object-level: request.user must be place owner of queue's place.
    Works when view.get_object() returns a Queue or Ticket
    """
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated and getattr(user, "role", "") == "place_admin"):
            return False
        # Ticket or Queue object
        if hasattr(obj, "queue") and hasattr(obj.queue, "place"):
            return obj.queue.place.owner == user
        if hasattr(obj, "place"):
            return obj.place.owner == user
        return False
