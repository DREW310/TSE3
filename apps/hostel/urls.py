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
    
    # Maintenance request URLs
    path('maintenance/submit/', views.submit_maintenance_request, name='submit_maintenance_request'),
    path('maintenance/my-requests/', views.my_maintenance_requests, name='my_maintenance_requests'),
    path('maintenance/all-requests/', views.all_maintenance_requests, name='all_maintenance_requests'),
    path('maintenance/manage/<int:request_id>/', views.manage_maintenance_request, name='manage_maintenance_request'),
    path('applications/', views.all_applications, name='all_applications'),
    path('semesters/', views.list_semesters, name='list_semesters'),
    path('semesters/add/', views.add_semester, name='add_semester'),
    path('semesters/edit/<int:semester_id>/', views.edit_semester, name='edit_semester'),
    path('semesters/delete/<int:semester_id>/', views.delete_semester, name='delete_semester'),
    path('applications/manage/<int:application_id>/', views.manage_application, name='manage_application'),
    path('applications/assign-room/<int:application_id>/', views.assign_room, name='assign_room'),
    path('my-room/', views.my_room, name='my_room'),
    path('applications/delete/<int:application_id>/', views.delete_application, name='delete_application'),
    path('rooms/', views.list_rooms, name='list_rooms'),
    path('rooms/add/', views.add_room, name='add_room'),
    path('rooms/edit/<int:room_id>/', views.edit_room, name='edit_room'),
    path('rooms/delete/<int:room_id>/', views.delete_room, name='delete_room'),
] 