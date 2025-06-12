from django import forms
from django.utils import timezone
from .models import HostelApplication, MaintenanceRequest, Semester, RoomAssignment, Room

# Form for semester management
class SemesterForm(forms.ModelForm):
    application_start_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text='The exact time applications will open on the start date'
    )
    
    application_end_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text='The exact time applications will close on the end date'
    )
    
    class Meta:
        model = Semester
        fields = ['name', 'start_date', 'end_date', 'application_start', 'application_end', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024/2025 Trimester 1'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'application_start': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'application_end': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'name': 'Enter a descriptive name for this semester',
            'start_date': 'The date when the semester begins',
            'end_date': 'The date when the semester ends',
            'application_start': 'The date when students can start applying',
            'application_end': 'The last date students can submit applications',
            'is_active': 'When checked, applications will be visible to students during the application period. If unchecked, applications will be hidden regardless of dates.'
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        application_start = cleaned_data.get('application_start')
        application_end = cleaned_data.get('application_end')

        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'End date must be after start date.')
        
        if application_start and application_end and application_end <= application_start:
            self.add_error('application_end', 'Application end date must be after application start date.')
        
        return cleaned_data

# Form for students to apply for hostel accommodation
class HostelApplicationForm(forms.ModelForm):
    price = forms.CharField(
        label='Estimated Total Price (RM)',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'disabled': 'disabled'}),
        help_text='This is the estimated total price for your selection.'
    )
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Select the date you want to start living in the hostel.'
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Select the date you want to leave the hostel.'
    )

    class Meta:
        model = HostelApplication
        fields = ['room_type', 'semester', 'start_date', 'end_date']
        widgets = {
            'room_type': forms.Select(attrs={
                'class': 'form-control',
                'title': 'Select your preferred room type',
                'onchange': 'updatePrice()'
            }),
            'semester': forms.Select(attrs={
                'class': 'form-control',
                'title': 'Select the semester you are applying for',
                'onchange': 'updatePrice()'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semester'].queryset = Semester.objects.filter(is_active=True)
        self.fields['semester'].help_text = 'If the semester you want is not listed, please contact staff.'
        self.fields['price'].initial = ''

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'End date must be after start date.')
        return cleaned_data

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['request_type', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please describe the issue in detail...',
                'minlength': '10',
                'maxlength': '500'
            }),
            'request_type': forms.Select(attrs={
                'class': 'form-control',
                'title': 'Select the type of maintenance required'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
                'title': 'Select the priority level of your request'
            })
        }

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 10:
            raise forms.ValidationError('Please provide a more detailed description (minimum 10 characters).')
        if len(description) > 500:
            raise forms.ValidationError('Description is too long (maximum 500 characters).')
        return description

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        priority = cleaned_data.get('priority')
        
        # Set high priority for urgent issues
        if request_type in ['electrical', 'plumbing'] and priority == 'low':
            cleaned_data['priority'] = 'medium'
            self.add_error('priority', 'Electrical and plumbing issues are automatically set to medium priority.')
        
        return cleaned_data 

class RoomAssignmentForm(forms.ModelForm):
    class Meta:
        model = RoomAssignment
        fields = ['room', 'start_date', 'end_date', 'payment_status']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        start_date = kwargs.pop('start_date', None)
        end_date = kwargs.pop('end_date', None)
        application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        qs = Room.objects.filter(status='available')
        if application:
            qs = qs.filter(room_type=application.room_type)

        if start_date and end_date:
            available_room_ids = [room.id for room in qs if not room.is_full_for_period(start_date, end_date)]
            self.fields['room'].queryset = qs.filter(id__in=available_room_ids)
        else:
            self.fields['room'].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if room and start_date and end_date and room.is_full_for_period(start_date, end_date):
            self.add_error('room', 'This room is fully booked for the selected period.')
        return cleaned_data 