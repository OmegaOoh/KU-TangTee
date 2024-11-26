"""Routing path for websocket."""
from django.urls import path
from chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:activity_id>", ChatConsumer.as_asgi()),
]
