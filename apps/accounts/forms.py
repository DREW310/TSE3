from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class StudentRegistrationForm(UserCreationForm):
    """
    Form for student registration
    This extends Django's built-in UserCreationForm but adds our custom fields
    """
    
    # Add extra fields we need for students
    student_id = forms.CharField(
        max_length=20,
        help_text="Enter your MMU Student ID",
        required=True
    )
    
    phone_number = forms.CharField(
        max_length=15,
        help_text="Enter your contact number",
        required=True
    )
    
    emergency_contact = forms.CharField(
        max_length=100,
        help_text="Name and contact number of emergency contact",
        required=True
    )
    
    class Meta:
        model = User
        # Fields that will show up in the form
        fields = [
            'username',
            'email',
            'student_id',
            'phone_number',
            'emergency_contact',
            'password1',
            'password2',
        ]
    
    def save(self, commit=True):
        # Get the user object but don't save it yet
        user = super().save(commit=False)
        # Set additional fields
        user.user_type = User.STUDENT
        user.is_profile_complete = True
        # Now save if commit is True
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information
    This is simpler than the registration form since we don't need password fields
    """
    
    class Meta:
        model = User
        fields = [
            'email',
            'phone_number',
            'emergency_contact',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required for profile completion
        for field in self.fields:
            self.fields[field].required = True 


class StaffRegistrationForm(UserCreationForm):
    """
    Form for staff registration
    Extends UserCreationForm, sets user_type to STAFF
    """
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.STAFF
        if commit:
            user.save()
        return user 