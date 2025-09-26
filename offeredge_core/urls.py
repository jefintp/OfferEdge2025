from django.contrib import admin
from django.urls import path, include
from users.views import dashboard_view
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('offeredge_core.homeurl')),  # homepage routing
    path('', include('users.urls')), # user authentication routing
    path('dashboard/', dashboard_view, name='dashboard'),
    path('users/', include('users.urls')),
    path('requirements/', include('requirements.urls')),
    path('quotes/', include('quotes.urls')),
    path('moderation/', include('moderation.urls')),
    path('deals/', include('deals.urls')),




]