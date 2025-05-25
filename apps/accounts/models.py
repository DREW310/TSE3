from django.contrib.auth.models import AbstractUser
from django.db import models

# Custom User model that extends Django's built-in AbstractUser
# This allows us to add our own fields while keeping all the good stuff Django provides
class User(AbstractUser):
    # User types
    STUDENT = 'student'
    STAFF = 'staff'
    ADMIN = 'admin'
    
    USER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (STAFF, 'Staff'),
        (ADMIN, 'Admin'),
    ]

    # Student types
    STUDENT_TYPE_CHOICES = [
        ('local', 'Local Student'),
        ('international', 'International Student'),
    ]

    # Gender choices
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    # Basic fields
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default=STUDENT)
    student_type = models.CharField(max_length=15, choices=STUDENT_TYPE_CHOICES, null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    home_address = models.CharField(max_length=255, null=True, blank=True)
    id_number = models.CharField(max_length=20, null=True, blank=True, help_text='IC No. or Passport No.')
    
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

    def is_local_student(self):
        """
        Quick way to check if user is a local student
        Usage: if user.is_local_student():
        """
        return self.user_type == self.STUDENT and self.student_type == 'local'

    def is_international_student(self):
        """
        Quick way to check if user is an international student
        Usage: if user.is_international_student():
        """
        return self.user_type == self.STUDENT and self.student_type == 'international'
