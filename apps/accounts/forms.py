from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
import re
from datetime import datetime

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
]

class StudentRegistrationForm(UserCreationForm):
    """
    Form for student registration
    This extends Django's built-in UserCreationForm but adds our custom fields
    """
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="First Name",
        help_text="Enter your first name"
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Last Name",
        help_text="Enter your last name"
    )
    
    student_type = forms.ChoiceField(
        choices=User.STUDENT_TYPE_CHOICES,
        help_text="Select your student type",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control bg-light'})
    )
    
    student_id = forms.CharField(
        max_length=20,
        help_text="Enter your University Student ID (e.g., A123456)",
        required=True,
        label="Student ID"
    )
    
    id_number = forms.CharField(
        max_length=20,
        help_text="If you are a local student, enter your Malaysian IC No. (e.g., 990101-14-5678). If international, enter your Passport No. (e.g., A1234567)",
        required=True,
        label="IC No. / Passport No."
    )
    
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        help_text="Select your gender (Male or Female)",
        required=True,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-control bg-light'})
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="For international students, enter your date of birth (e.g., 2001-01-01). For local students, enter your date of birth as per your IC.",
        label="Date of Birth"
    )
    
    phone_number = forms.CharField(
        max_length=15,
        help_text="Enter your Malaysian phone number (e.g., 012-3456789)",
        required=True
    )
    
    emergency_contact = forms.CharField(
        max_length=100,
        help_text="Name and phone number of emergency contact (e.g., Ali, 019-8765432)",
        required=True
    )
    
    home_address = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 2}),
        help_text="Enter your home address (e.g., 123, Jalan Example, 43000 Kajang, Selangor)",
        required=True,
        label="Home Address"
    )
    
    email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'student_type',
            'student_id',
            'id_number',
            'gender',
            'date_of_birth',
            'phone_number',
            'emergency_contact',
            'home_address',
            'password1',
            'password2',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.help_text = ''
            if field.required:
                field.label_suffix = ' <span class="text-danger">*</span>'
            # Add Bootstrap class for consistent styling
            if field.widget.__class__.__name__ != 'CheckboxInput':
                existing_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing_classes + ' form-control').strip()

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        student_type = self.cleaned_data.get('student_type')
        if student_type == 'local':
            # Malaysian IC format: 6 digits - 2 digits - 4 digits
            if not re.match(r'^\d{6}-\d{2}-\d{4}$', id_number):
                raise forms.ValidationError('Please enter a valid Malaysian IC No. (e.g., 990101-14-5678)')
        elif student_type == 'international':
            # Passport: at least 6 alphanumeric characters
            if not re.match(r'^[A-Za-z0-9]{6,}$', id_number):
                raise forms.ValidationError('Please enter a valid Passport No. (e.g., A1234567)')
        return id_number

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            student_id = student_id.upper()
        # MMU: 9 or 10 alphanumeric characters (uppercase letters and digits)
        if not re.match(r'^[A-Z0-9]{9,10}$', student_id):
            raise forms.ValidationError('Please enter a valid Student ID (e.g., 1211109457 or 243UT246WP)')
        # Uniqueness check (case-insensitive)
        if User.objects.filter(student_id__iexact=student_id).exists():
            raise forms.ValidationError('This Student ID is already registered.')
        return student_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        student_type = cleaned_data.get('student_type')
        id_number = cleaned_data.get('id_number')
        dob = cleaned_data.get('date_of_birth')
        # For local students, auto-extract DOB from IC No.
        if student_type == 'local' and id_number:
            try:
                ic_dob = id_number[:6]  # YYMMDD
                year = int(ic_dob[:2])
                month = int(ic_dob[2:4])
                day = int(ic_dob[4:6])
                # Assume 1900s for year >= 30, else 2000s (simple logic)
                year += 1900 if year >= 30 else 2000
                dob_value = datetime(year, month, day).date()
                cleaned_data['date_of_birth'] = dob_value
            except Exception:
                self.add_error('id_number', 'IC No. does not contain a valid date of birth.')
        elif student_type == 'international':
            if not dob:
                self.add_error('date_of_birth', 'Please enter your date of birth.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.STUDENT
        user.student_id = self.cleaned_data['student_id'].upper()
        user.student_type = self.cleaned_data['student_type']
        user.phone_number = self.cleaned_data['phone_number']
        user.emergency_contact = self.cleaned_data['emergency_contact']
        user.gender = self.cleaned_data['gender']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        user.home_address = self.cleaned_data['home_address']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information
    This is simpler than the registration form since we don't need password fields
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="First Name",
        help_text="Enter your first name"
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Last Name",
        help_text="Enter your last name"
    )
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'student_type',
            'student_id',
            'id_number',
            'gender',
            'date_of_birth',
            'phone_number',
            'emergency_contact',
            'home_address',
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required for profile completion
        for field in self.fields:
            self.fields[field].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


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