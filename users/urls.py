from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),         # Registration
    path('login/', views.login_view, name='login'),            # Login
    path('logout/', views.logout_view, name='logout'),         # Logout
    path('dashboard/', views.dashboard_view, name='dashboard'),# Protected dashboard
  #  path('test/', views.test_user_save, name='test_user_save') # MongoDB test
    path('dashboard/', views.dashboard_view),
    # path('debug-quotes/', views.debug_quotes_view),  # ✅ Add this line

]