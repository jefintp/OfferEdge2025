from django.urls import path
from .views import (
    moderation_dashboard,
    ban_user_view,
    unban_user_view,
    delete_user_view,
    finalize_quote_view as mod_finalize_quote_view,
    delete_quote_view as mod_delete_quote_view,
    delete_requirement_mod_view,
)

urlpatterns = [
    path('', moderation_dashboard, name='moderation_dashboard'),
    path('ban_user/<str:user_id>/', ban_user_view, name='ban_user'),
    path('unban_user/<str:user_id>/', unban_user_view, name='unban_user'),
    path('delete_user/<str:user_id>/', delete_user_view, name='delete_user'),
    path('finalize_quote/<str:quote_id>/', mod_finalize_quote_view, name='mod_finalize_quote'),
    path('delete_quote/<str:quote_id>/', mod_delete_quote_view, name='mod_delete_quote'),
    path('delete_requirement/<str:req_id>/', delete_requirement_mod_view, name='mod_delete_requirement'),
]
