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
            # Save the user but do NOT log them in
            form.save()
            # Show success message
            messages.success(request, 'Registration successful! Please log in with your new credentials.')
            return redirect('accounts:login')
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
    from apps.hostel.models import RoomAssignment, Payment
    
    # Find the latest room assignment linked to an approved application
    latest_assignment = RoomAssignment.objects.filter(
        student=request.user,
        # Check if the related application is approved using the new foreign key
        hostel_application__status='approved'
    ).order_by('-date_assigned').first()

    # Fetch payments related to the latest assignment
    payments = []
    if latest_assignment:
        payments = Payment.objects.filter(room_assignment=latest_assignment).order_by('-date_paid')

    # Count active maintenance requests
    active_maintenance_requests_count = request.user.maintenance_requests.filter(
        status__in=['pending', 'in_progress']
    ).count()

    context = {
        'user': request.user,
        'hostel_applications': request.user.hostel_applications.all(),
        'maintenance_requests': request.user.maintenance_requests.all(),
        'active_maintenance_requests_count': active_maintenance_requests_count,
        'latest_assignment': latest_assignment,
        'payments': payments,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def staff_dashboard(request):
    """
    Staff dashboard view
    Shows overview for staff users
    """
    from apps.hostel.models import HostelApplication, MaintenanceRequest
    
    context = {
        'user': request.user,
        'hostel_applications': HostelApplication.objects.all(),
        'maintenance_requests': MaintenanceRequest.objects.all(),
    }
    return render(request, 'accounts/dashboard.html', context)
