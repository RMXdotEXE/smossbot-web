from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/localhost:5000', consumers.Consumer.as_asgi())
]