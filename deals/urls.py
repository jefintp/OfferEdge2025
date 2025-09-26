from django.urls import path
from .views import finalize_quote_view

urlpatterns = [
    path('finalize/<quote_id>/', finalize_quote_view, name='finalize_quote'),
]