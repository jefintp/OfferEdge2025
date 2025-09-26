from django.urls import path
from . import views
from requirements.views import delete_requirement_view

urlpatterns = [
    path('post/', views.post_requirement_view, name='post_requirement'),
    path('mine/', views.my_requirements_view, name='my_requirements'),
    path('delete/<str:reqid>', delete_requirement_view),  # ✅ remove "requirements/" prefix
]