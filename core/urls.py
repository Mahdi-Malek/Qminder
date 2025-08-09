from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

# Initialize router
router = DefaultRouter()
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'users', UserManagementViewSet, basename='user')

urlpatterns = [
    # Places related URLs
    path("places/nearby/", NearbyPlacesView.as_view(), name="nearby-places"),
    
    # Queue related URLs
    path("queue/<int:place_id>/", QueueStatusView.as_view(), name="queue-status"),
    path("queue/<int:place_id>/join/", JoinQueueView.as_view(), name="join-queue"),
    path("queue/leave/<int:ticket_id>/", LeaveQueueView.as_view(), name="leave-queue"),
    
    # Authentication URLs
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),  # Note: duplicate of token-obtain-pair
    
    # User management URLs (using viewsets)
    path("users/", UserManagementViewSet.as_view({"get": "list"}), name="user-list"),
    path("users/<int:pk>/", UserManagementViewSet.as_view({"get": "retrieve"}), name="user-detail"),
    path("users/<int:pk>/role/", UserManagementViewSet.as_view({"patch": "update_role"}), name="user-update-role"),
]

# Add router URLs
urlpatterns += router.urls

# Serve media files in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)