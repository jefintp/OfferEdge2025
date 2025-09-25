from django.urls import path
from . import views

urlpatterns = [
    path('post/', views.post_requirement_view, name='post_requirement'),
    path('mine/', views.my_requirements_view, name='my_requirements'),
]