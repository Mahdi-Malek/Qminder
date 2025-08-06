from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

urlpatterns = [
    path('places/nearby/', NearbyPlacesView.as_view()),
    path('queue/<int:place_id>/', QueueStatusView.as_view()),
    path('queue/<int:place_id>/join/', JoinQueueView.as_view()),
    path('queue/leave/<int:ticket_id>/', LeaveQueueView.as_view()),
]

urlpatterns += [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


