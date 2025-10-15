from django.urls import path
from .views import finalize_quote_view, deal_dashboard_view

urlpatterns = [
    path('finalize/<quote_id>/', finalize_quote_view, name='finalize_quote'),
    #  path('debug/quote/<str:quote_id>/', debug_quote_requirement, name='debug_quote')
    path("dashboard/", deal_dashboard_view, name="deal_dashboard")
]