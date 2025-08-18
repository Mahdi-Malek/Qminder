from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NearbyPlacesView, JoinQueueView, LeaveQueueView,
    PlaceViewSet, QueueAdminViewSet, AdminTicketsView,
    NotificationListView, MarkNotificationReadView, RegisterView,
    AnalyticsView, UserProfileView, LogoutView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # برای login
    TokenRefreshView,      # برای refresh
)

router = DefaultRouter()
router.register(r"places", PlaceViewSet, basename="place")
router.register(r"admin/queues", QueueAdminViewSet, basename="admin-queues")

urlpatterns = [
    path("places/nearby/", NearbyPlacesView.as_view(), name="places-nearby"),
    path("queues/<int:place_id>/join/", JoinQueueView.as_view(), name="join-queue"),
    path("tickets/<int:ticket_id>/leave/", LeaveQueueView.as_view(), name="leave-queue"),
    path("admin/queues/<int:queue_id>/tickets/", AdminTicketsView.as_view({"get": "list", "patch": "partial_update"}), name="admin-tickets"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("auth/register/", RegisterView.as_view(), name="register"), # register
    path("auth/user/", UserProfileView.as_view(), name="user_profile"), # user profile
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"), # login 
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # refresh
    path("auth/logout/", LogoutView.as_view(), name="logout"), # logout

]

urlpatterns += router.urls
