from django.urls import path
from .views import moderation_dashboard

urlpatterns = [
    path('', moderation_dashboard, name='moderation_dashboard'),
]