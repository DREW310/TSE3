from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import StudentRegistrationForm, ProfileUpdateForm, StaffRegistrationForm
from django.utils import timezone

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
    from apps.hostel.models import RoomAssignment, Payment, Semester
    
    # Find the latest room assignment linked to an approved application
    latest_assignment = RoomAssignment.objects.filter(
        student=request.user,
        # Check if the related application is approved using the new foreign key
        hostel_application__status='approved'
    ).order_by('-date_assigned').first()

    # Fetch payments related to the latest assignment
    payments = []
    payment_status = 'pending'
    if latest_assignment:
        payments = Payment.objects.filter(room_assignment=latest_assignment).order_by('-date_paid')
        # Check if any payment is completed
        if payments.filter(status='completed').exists():
            payment_status = 'completed'

    # Count active maintenance requests
    active_maintenance_requests_count = request.user.maintenance_requests.filter(
        status__in=['pending', 'in_progress']
    ).count()
    
    # Check if there are any active application periods
    now = timezone.now()
    active_application_period = Semester.objects.filter(
        is_active=True,
        application_start__lte=now,
        application_end__gte=now
    ).exists()
    
    # Get the latest application
    latest_application = request.user.hostel_applications.order_by('-date_applied').first()
    
    # Check if the student has any pending/approved applications
    has_active_application = request.user.hostel_applications.filter(
        status__in=['pending', 'approved']
    ).exists()
    
    has_other_active_application = False
    if latest_application and latest_application.status == 'rejected':
        # Check if the student has any other pending or approved applications
        has_other_active_application = request.user.hostel_applications.filter(
            status__in=['pending', 'approved']
        ).exclude(id=latest_application.id).exists()
    
    # A student can apply again if:
    # 1. The application period is active AND
    # 2. They have no active applications OR their only application is rejected
    can_apply_again = active_application_period and (not has_active_application or 
                                                    (latest_application and 
                                                     latest_application.status == 'rejected' and 
                                                     not has_other_active_application))

    context = {
        'user': request.user,
        'hostel_applications': request.user.hostel_applications.all().order_by('-date_applied'),
        'maintenance_requests': request.user.maintenance_requests.all(),
        'active_maintenance_requests_count': active_maintenance_requests_count,
        'latest_assignment': latest_assignment,
        'payments': payments,
        'payment_status': payment_status,
        'active_application_period': active_application_period,
        'can_apply_again': can_apply_again,
        'has_other_active_application': has_other_active_application,
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
