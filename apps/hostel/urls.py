from django.urls import path
from . import views

# This helps Django identify our app in URL patterns
app_name = 'hostel'

# URL patterns for the hostel app
urlpatterns = [
    # Student applies for hostel accommodation
    path('apply/', views.apply_for_hostel, name='apply'),
    # Student views their application status
    path('my-application/', views.my_hostel_application, name='my_application'),
] 