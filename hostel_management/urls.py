"""
URL Configuration for hostel_management project.
Written in a student-friendly way with clear comments.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # User authentication and profile management
    path('accounts/', include('apps.accounts.urls')),
    
    # Hostel management features (student applications, etc.)
    path('hostel/', include('apps.hostel.urls')),
    
    # Redirect root URL to login page
    path('', RedirectView.as_view(pattern_name='accounts:login'), name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
