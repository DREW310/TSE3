from django.contrib.auth.models import AbstractUser
from django.db import models

# Custom User model that extends Django's built-in AbstractUser
# This allows us to add our own fields while keeping all the good stuff Django provides
class User(AbstractUser):
    # Constants for user types - makes it easy to understand what type of user we're dealing with
    STUDENT = 'student'
    STAFF = 'staff'
    ADMIN = 'admin'
    
    # Choices for user_type field - this creates a dropdown in forms
    USER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (STAFF, 'Staff'),
        (ADMIN, 'Admin'),
    ]
    
    # Custom fields we need for our hostel system
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=STUDENT,  # Most users will be students
        help_text="Type of user account"  # This shows up in the admin panel
    )
    
    # Student-specific fields
    student_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,  # Not required for admin users
        help_text="MMU Student ID number"
    )
    
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Contact phone number"
    )
    
    # This helps us know if a student has completed their profile
    is_profile_complete = models.BooleanField(
        default=False,
        help_text="Whether the user has completed their profile information"
    )
    
    # This is useful for sending important notifications
    emergency_contact = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Emergency contact information"
    )
    
    def __str__(self):
        """
        This shows up in the admin panel and makes it easy to identify users
        Example: "john_doe (Student)" or "admin_user (Admin)"
        """
        return f"{self.username} ({self.get_user_type_display()})"
    
    def is_student(self):
        """
        Quick way to check if user is a student
        Usage: if user.is_student():
        """
        return self.user_type == self.STUDENT
    
    def is_hostel_admin(self):
        """
        Quick way to check if user is an admin
        Usage: if user.is_hostel_admin():
        """
        return self.user_type == self.ADMIN
    
    def is_staff_user(self):
        """
        Quick way to check if user is a staff
        Usage: if user.is_staff_user():
        """
        return self.user_type == self.STAFF
