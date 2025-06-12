from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from .models import User
import re
from datetime import datetime
from django.utils.translation import gettext_lazy as _

GENDER_CHOICES = [
    ('', '-- Select Gender --'),
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
        widget=forms.TextInput(attrs={'placeholder': 'e.g., John'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Smith'})
    )
    
    student_type = forms.ChoiceField(
        choices=[('', '-- Select Student Type --')] + list(User.STUDENT_TYPE_CHOICES),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    student_id = forms.CharField(
        max_length=20,
        required=True,
        label="Student ID",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 1211109457 or 243WT256WL'})
    )
    
    id_number = forms.CharField(
        max_length=20,
        required=True,
        label="IC No. / Passport No.",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 990101-14-5678 or A1234567'})
    )
    
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'placeholder': 'YYYY-MM-DD'
        }),
        label="Date of Birth"
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., +601110599609'})
    )
    
    emergency_contact = forms.CharField(
        max_length=100,
        required=True,
        label="Emergency Contact",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Ali, +601110599609'})
    )
    
    home_address = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your permanent home address'}),
        required=True,
        label="Home Address"
    )
    
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., john@example.com'
        })
    )
    
    class Meta:
        model = User
        fields = [
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
        # Remove username field help text
        if 'username' in self.fields:
            del self.fields['username']
            
        # Update password help texts to be more user-friendly
        self.fields['password1'].help_text = 'At least 8 characters with letters and numbers'
        self.fields['password2'].help_text = 'Enter the same password again'
        
        # Add Bootstrap classes for consistent styling
        for field_name, field in self.fields.items():
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
        user.username = self.cleaned_data['student_id'].upper()  # Use student_id as username
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


class StudentAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses Student ID instead of username
    """
    username = forms.CharField(
        label=_("Student ID"),
        widget=forms.TextInput(attrs={'autofocus': True}),
        error_messages={
            'required': _('Please enter your Student ID'),
        }
    )
    
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        error_messages={
            'required': _('Please enter your password'),
        }
    )
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct Student ID and password. Note that both fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

class StudentPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form that validates the email exists in our system
    """
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError(_("We couldn't find an account with that email address. Please check and try again."))
        return email 