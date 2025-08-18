import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

# تنظیم متغیر محیطی قبل از هر چیز دیگر
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartqueue.settings')

# راه‌اندازی Django
django.setup()

from core.routing import websocket_urlpatterns

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),



})