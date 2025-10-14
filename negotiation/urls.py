from django.urls import path
from negotiation.views import (
    start_chat_view, chat_room_view,
    send_message_view, chat_messages_partial, chat_dashboard_view
)

urlpatterns = [
    path("chat/dashboard/", chat_dashboard_view, name="chat_dashboard"),  # ✅ static first
    path("chat/start/<str:quote_id>/", start_chat_view, name="start_chat"),
    path("chat/send/<str:session_id>/", send_message_view, name="send_message"),
    path("chat/messages/<str:session_id>/", chat_messages_partial, name="chat_messages_partial"),
    path("chat/<str:session_id>/", chat_room_view, name="chat_room"),  # ✅ dynamic last
]