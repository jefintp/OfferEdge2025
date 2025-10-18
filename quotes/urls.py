from django.urls import path
from . import views

urlpatterns = [
    path('explore/', views.explore_requirements_view, name='explore_quotes'),
    path('place/<str:reqid>/', views.place_quote_view, name='place_quote'),
    path('my/', views.my_quotes_view, name='my_quotes'),
    path('for/<str:reqid>/', views.quotes_for_requirement_view, name='quotes_for_requirement'),
    path('delete/<str:quote_id>/', views.delete_quote_view, name='delete_quote'),
]
