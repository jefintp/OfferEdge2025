from django.urls import path
from .views import finalize_quote_view, deal_dashboard_view, finalized_deals_view

urlpatterns = [
    path('finalize/<quote_id>/', finalize_quote_view, name='finalize_quote'),
    path('finalized/', finalized_deals_view, name='finalized_deals'),
    path("dashboard/", deal_dashboard_view, name="deal_dashboard"),
]
