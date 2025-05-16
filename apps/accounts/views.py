from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import StudentRegistrationForm, ProfileUpdateForm, StaffRegistrationForm

def student_register(request):
    """
    View for student registration
    Shows registration form and handles form submission
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        # Create form with submitted data
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user and log them in
            user = form.save()
            login(request, user)
            # Show success message
            messages.success(request, 'Registration successful! Welcome to MMU Hostel Management System.')
            return redirect('accounts:dashboard')
    else:
        # Show empty form for GET request
        form = StudentRegistrationForm()
    
    # Show the registration page with the form
    return render(request, 'accounts/register.html', {'form': form})

@user_passes_test(lambda u: u.is_hostel_admin())
def staff_register(request):
    """
    View for staff registration
    Only admin users can add staff
    """
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Staff registration successful!')
            return redirect('accounts:staff_dashboard')
    else:
        form = StaffRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required  # Makes sure only logged-in users can access this view
def profile(request):
    """
    View for viewing and updating profile
    Shows profile form and handles form submission
    """
    if request.method == 'POST':
        # Create form with submitted data
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            # Save the updated profile
            form.save()
            # Show success message
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        # Show form with current user data for GET request
        form = ProfileUpdateForm(instance=request.user)
    
    # Show the profile page with the form
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def student_dashboard(request):
    """
    Student dashboard view
    Shows overview of student's hostel status, applications, etc.
    """
    # Get all the information we need to show on dashboard
    context = {
        'user': request.user,
        # We'll add more context data here when we create other apps
        # Like hostel application status, room details, etc.
    }
    return render(request, 'accounts/dashboard.html', context)

def staff_dashboard(request):
    """
    Staff dashboard view
    Shows overview for staff users
    """
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/staff_dashboard.html', context)
