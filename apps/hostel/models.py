from django.db import models
from apps.accounts.models import User  # Import our custom User model

# Create your models here.

# Model to store hostel applications submitted by students
class HostelApplication(models.Model):
    # Link each application to a student user
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # If the user is deleted, delete their applications too
        related_name='hostel_applications',
        help_text="The student who submitted this application"
    )

    # Room type choices (single, double, etc.)
    ROOM_TYPE_CHOICES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('triple', 'Triple Room'),
    ]
    room_type = models.CharField(
        max_length=10,
        choices=ROOM_TYPE_CHOICES,
        help_text="Type of room the student is applying for"
    )

    # Semester for which the application is made
    semester = models.CharField(
        max_length=20,
        help_text="Semester (e.g., 2023/2024 Semester 1)"
    )

    # Application status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the application"
    )

    # Date and time when the application was submitted
    date_applied = models.DateTimeField(
        auto_now_add=True,
        help_text="When the application was submitted"
    )

    def __str__(self):
        # This will show up in the admin panel and makes it easy to identify applications
        return f"{self.student.username} - {self.room_type} ({self.status})"
