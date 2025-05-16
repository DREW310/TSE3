from django import forms
from .models import HostelApplication

# Form for students to apply for hostel accommodation
class HostelApplicationForm(forms.ModelForm):
    class Meta:
        model = HostelApplication
        # Fields that students can fill out
        fields = ['room_type', 'semester']
        # Add simple labels and help texts for clarity
        labels = {
            'room_type': 'Room Type',
            'semester': 'Semester',
        }
        help_texts = {
            'room_type': 'Choose the type of room you want to apply for.',
            'semester': 'Enter the semester (e.g., 2023/2024 Semester 1).',
        } 