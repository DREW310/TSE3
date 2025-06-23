from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import HostelApplicationForm, MaintenanceRequestForm, RoomAssignmentForm, SemesterForm
from .models import HostelApplication, MaintenanceRequest, Room, RoomAssignment, Semester, get_room_price, Payment
from django import forms
from datetime import date
from django.forms import modelform_factory
import datetime
from django.http import JsonResponse
import json
from django.db.models import Count, Q
from collections import defaultdict

# Create your views here.

# View for students to apply for hostel accommodation
@login_required
def apply_for_hostel(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can apply for hostel accommodation.')
        return redirect('accounts:dashboard')

    # Check if user already has a pending/approved application
    existing_application = HostelApplication.objects.filter(
        student=request.user,
        status__in=['pending', 'approved']
    ).order_by('-date_applied').first()

    if request.method == 'POST':
        form = HostelApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = request.user
            
            # Check if auto-rejection is needed before saving
            semester = application.semester
            room_type = application.room_type
            
            # Count approved applications for this semester and room type
            approved_single = HostelApplication.objects.filter(semester=semester, room_type='single', status='approved').count()
            approved_double = HostelApplication.objects.filter(semester=semester, room_type='double', status='approved').count()
            quota_single = semester.quota_single
            quota_double = semester.quota_double * 2  # double room quota is number of students
            
            # Calculate remaining quota
            remaining_single = max(0, quota_single - approved_single)
            remaining_double = max(0, quota_double - approved_double)
            
            # Check for available rooms
            available_single_rooms = 0
            available_double_rooms = 0
            
            single_rooms = Room.objects.filter(room_type='single', status='available')
            for room in single_rooms:
                if not room.is_full_for_period(application.start_date, application.end_date):
                    available_single_rooms += 1
                    
            double_rooms = Room.objects.filter(room_type='double', status='available')
            for room in double_rooms:
                if not room.is_full_for_period(application.start_date, application.end_date):
                    # Count available spots in double rooms (could be 1 or 2 per room)
                    capacity = room.capacity
                    current_occupants = room.get_occupancy_count()
                    available_spots = capacity - current_occupants
                    available_double_rooms += available_spots
            
            # Save the application
            application.save()
            
            # Check if auto-rejection is needed
            auto_rejected = False
            if room_type == 'single' and (remaining_single <= 0 or available_single_rooms <= 0):
                application.status = 'rejected'
                application.rejection_reason = 'Auto-rejected: No quota or rooms available for single rooms.'
                application.is_auto_rejected = True
                application.save()
                auto_rejected = True
                messages.warning(request, 'Your application has been automatically rejected due to no quota or rooms available for single rooms.')
            elif room_type == 'double' and (remaining_double <= 0 or available_double_rooms <= 0):
                application.status = 'rejected'
                application.rejection_reason = 'Auto-rejected: No quota or rooms available for double rooms.'
                application.is_auto_rejected = True
                application.save()
                auto_rejected = True
                messages.warning(request, 'Your application has been automatically rejected due to no quota or rooms available for double rooms.')
            
            if not auto_rejected:
                messages.success(request, 'Your hostel application has been submitted successfully!')
                
            return redirect('hostel:my_application')
    else:
        form = HostelApplicationForm(user=request.user)

    # Get semester data for frontend calculations
    now = timezone.now()
    active_semesters = Semester.objects.filter(
        is_active=True,
        application_start__lte=now,
        application_end__gte=now
    )
    semester_data = {
        str(semester.id): {
            'start_date': semester.start_date.isoformat(),
            'end_date': semester.end_date.isoformat(),
            'name': semester.name
        } for semester in active_semesters
    }

    context = {
        'form': form,
        'already_applied': existing_application is not None,
        'semester_data': json.dumps(semester_data)
    }
    return render(request, 'hostel/apply.html', context)

# View for students to see their hostel application status
@login_required
def my_hostel_application(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view hostel applications.')
        return redirect('accounts:dashboard')

    application = HostelApplication.objects.filter(student=request.user).order_by('-date_applied').first()
    semester_name = application.semester.name if application else None
    
    # Auto-rejection check for pending applications
    if application and application.status == 'pending':
        semester = application.semester
        # Count approved applications for this semester and room type
        approved_single = HostelApplication.objects.filter(semester=semester, room_type='single', status='approved').count()
        approved_double = HostelApplication.objects.filter(semester=semester, room_type='double', status='approved').count()
        quota_single = semester.quota_single
        quota_double = semester.quota_double * 2  # double room quota is number of students
        
        # Calculate remaining quota
        remaining_single = max(0, quota_single - approved_single)
        remaining_double = max(0, quota_double - approved_double)
        
        # Check for available rooms
        from .models import Room
        available_single_rooms = 0
        available_double_rooms = 0
        
        single_rooms = Room.objects.filter(room_type='single', status='available')
        for room in single_rooms:
            if not room.is_full_for_period(application.start_date, application.end_date):
                available_single_rooms += 1
                
        double_rooms = Room.objects.filter(room_type='double', status='available')
        for room in double_rooms:
            if not room.is_full_for_period(application.start_date, application.end_date):
                # Count available spots in double rooms (could be 1 or 2 per room)
                capacity = room.capacity
                current_occupants = room.get_occupancy_count()
                available_spots = capacity - current_occupants
                available_double_rooms += available_spots
        
        # Auto-reject if no quota or rooms available
        if application.room_type == 'single' and (remaining_single <= 0 or available_single_rooms <= 0):
            application.status = 'rejected'
            application.rejection_reason = 'Auto-rejected: No quota or rooms available for single rooms.'
            application.is_auto_rejected = True
            application.save()
            messages.warning(request, 'Your application has been automatically rejected due to no quota or rooms available for single rooms.')
        elif application.room_type == 'double' and (remaining_double <= 0 or available_double_rooms <= 0):
            application.status = 'rejected'
            application.rejection_reason = 'Auto-rejected: No quota or rooms available for double rooms.'
            application.is_auto_rejected = True
            application.save()
            messages.warning(request, 'Your application has been automatically rejected due to no quota or rooms available for double rooms.')
    
    # Check if application period is still open for reapplication
    can_apply_again = False
    active_application_period = False
    has_other_active_application = False
    
    if application and application.status == 'rejected':
        now = timezone.now()
        # Check if there are any active semesters with open application periods
        active_semesters = Semester.objects.filter(
            is_active=True,
            application_start__lte=now,
            application_end__gte=now
        )
        active_application_period = active_semesters.exists()
        
        # Check if the student has any other pending or approved applications
        has_other_active_application = HostelApplication.objects.filter(
            student=request.user,
            status__in=['pending', 'approved']
        ).exclude(id=application.id).exists()
        
        # A student can apply again if the application period is active and they don't have other active applications
        can_apply_again = active_application_period and not has_other_active_application
    
    context = {
        'application': application, 
        'semester_name': semester_name,
        'can_apply_again': can_apply_again,
        'active_application_period': active_application_period,
        'has_other_active_application': has_other_active_application
    }
    return render(request, 'hostel/my_application.html', context)

# View for students to submit a maintenance request
@login_required
def submit_maintenance_request(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can submit maintenance requests.')
        return redirect('accounts:dashboard')

    # Check if student has an assigned room (either current or future)
    # First check for a current active assignment
    active_assignment = RoomAssignment.objects.filter(
        student=request.user,
        status='active',
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).first()
    
    # If no current assignment, check for a future assignment with completed payment
    if not active_assignment:
        active_assignment = RoomAssignment.objects.filter(
            student=request.user,
            status='active',
            payment_status='paid',
            hostel_application__status='approved'
        ).order_by('start_date').first()
    
    if not active_assignment:
        messages.error(request, 'You must have an active room assignment to submit maintenance requests.')
        return redirect('hostel:my_room')

    # Check if payment for this assignment is completed
    payment = active_assignment.payments.filter(status='completed').first()
    if not payment:
        messages.error(request, 'You can only submit maintenance requests after your hostel payment is marked as paid. Please pay at the counter and wait for staff to update your payment status.')
        return redirect('hostel:my_room')

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.student = request.user
            request_obj.room_number = active_assignment.room.room_number
            request_obj.save()
            messages.success(request, 'Your maintenance request has been submitted successfully!')
            return redirect('hostel:my_maintenance_requests')
        else:
            messages.error(request, 'Please correct the errors in your request.')
    else:
        form = MaintenanceRequestForm()
    
    return render(request, 'hostel/submit_maintenance_request.html', {
        'form': form,
        'room_number': active_assignment.room.room_number
    })

# View for students to see their maintenance requests
@login_required
def my_maintenance_requests(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view maintenance requests.')
        return redirect('accounts:dashboard')

    # Get all assignments for this student (current, past, and future)
    assignments = RoomAssignment.objects.filter(
        student=request.user,
        status__in=['active', 'completed'],
        hostel_application__status='approved'
    )
    
    trimester = request.GET.get('trimester')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Get all maintenance requests for this student
    requests = MaintenanceRequest.objects.filter(student=request.user)
    
    if trimester:
        # Filter by semester (trimester)
        filtered_assignments = assignments.filter(hostel_application__semester_id=trimester)
        room_numbers = filtered_assignments.values_list('room__room_number', flat=True)
        requests = requests.filter(room_number__in=room_numbers)
    
    if date_from:
        requests = requests.filter(date_submitted__date__gte=date_from)
    
    if date_to:
        requests = requests.filter(date_submitted__date__lte=date_to)
    
    requests = requests.order_by('-date_submitted')
    
    # Get all trimesters for filter dropdown
    trimesters = Semester.objects.all().order_by('-start_date')
    
    return render(request, 'hostel/my_maintenance_requests.html', {
        'requests': requests, 
        'trimesters': trimesters, 
        'selected_trimester': trimester
    })

# View for staff to see all maintenance requests
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def all_maintenance_requests(request):
    trimester = request.GET.get('trimester')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    requests = MaintenanceRequest.objects.all()
    if trimester:
        assignments = RoomAssignment.objects.filter(hostel_application__semester_id=trimester)
        room_numbers = assignments.values_list('room__room_number', flat=True)
        requests = requests.filter(room_number__in=room_numbers)
    if date_from:
        requests = requests.filter(date_submitted__date__gte=date_from)
    if date_to:
        requests = requests.filter(date_submitted__date__lte=date_to)
    requests = requests.order_by('-date_submitted')
    trimesters = Semester.objects.all().order_by('-start_date')
    return render(request, 'hostel/all_maintenance_requests.html', {'requests': requests, 'trimesters': trimesters, 'selected_trimester': trimester})

# View for staff to manage a specific maintenance request
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def manage_maintenance_request(request, request_id):
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        staff_notes = request.POST.get('staff_notes')
        if status == 'completed':
            maintenance_request.mark_completed(request.user)
            if staff_notes:
                maintenance_request.staff_notes = staff_notes
                maintenance_request.save()
            messages.success(request, 'Maintenance request marked as completed!')
        elif status in dict(MaintenanceRequest.STATUS_CHOICES):
            if maintenance_request.update_status(status, staff_notes):
                messages.success(request, 'Maintenance request updated successfully!')
            else:
                messages.error(request, 'Cannot update this request.')
        else:
            messages.error(request, 'Invalid status selected.')
        return redirect('hostel:all_maintenance_requests')
    return render(request, 'hostel/manage_maintenance_request.html', {
        'maintenance_request': maintenance_request
    })

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def manage_application(request, application_id):
    application = get_object_or_404(HostelApplication, id=application_id)
    semester = application.semester
    # Count approved applications for this semester and room type
    approved_single = HostelApplication.objects.filter(semester=semester, room_type='single', status='approved').count()
    approved_double = HostelApplication.objects.filter(semester=semester, room_type='double', status='approved').count()
    quota_single = semester.quota_single
    quota_double = semester.quota_double * 2  # double room quota is number of students
    
    # Calculate remaining quota
    remaining_single = max(0, quota_single - approved_single)
    remaining_double = max(0, quota_double - approved_double)
    
    # Check for available rooms
    from .models import Room
    available_single_rooms = 0
    available_double_rooms = 0
    
    single_rooms = Room.objects.filter(room_type='single', status='available')
    for room in single_rooms:
        if not room.is_full_for_period(application.start_date, application.end_date):
            available_single_rooms += 1
            
    double_rooms = Room.objects.filter(room_type='double', status='available')
    for room in double_rooms:
        if not room.is_full_for_period(application.start_date, application.end_date):
            # Count available spots in double rooms (could be 1 or 2 per room)
            capacity = room.capacity
            current_occupants = room.get_occupancy_count()
            available_spots = capacity - current_occupants
            available_double_rooms += available_spots
    
    # Debug information
    print(f"DEBUG: Application ID: {application.id}, Room Type: {application.room_type}")
    print(f"DEBUG: Quota - Single: {quota_single}, Double: {quota_double}")
    print(f"DEBUG: Approved - Single: {approved_single}, Double: {approved_double}")
    print(f"DEBUG: Remaining - Single: {remaining_single}, Double: {remaining_double}")
    print(f"DEBUG: Available Rooms - Single: {available_single_rooms}, Double: {available_double_rooms}")
    
    # Check if this specific application can be approved based on room type
    can_approve = True
    approval_blocked_reason = ""
    
    if application.room_type == 'single':
        if remaining_single <= 0:
            can_approve = False
            approval_blocked_reason = "Quota for single rooms has been reached."
            print(f"DEBUG: Can't approve - No quota for single rooms")
        elif available_single_rooms <= 0:
            can_approve = False
            approval_blocked_reason = "No available single rooms for the requested period."
            print(f"DEBUG: Can't approve - No available single rooms")
    else:  # double room
        if remaining_double <= 0:
            can_approve = False
            approval_blocked_reason = "Quota for double rooms has been reached."
            print(f"DEBUG: Can't approve - No quota for double rooms")
        elif available_double_rooms <= 0:
            can_approve = False
            approval_blocked_reason = "No available spots in double rooms for the requested period."
            print(f"DEBUG: Can't approve - No available double rooms")
    
    print(f"DEBUG: Final can_approve: {can_approve}, Reason: {approval_blocked_reason if not can_approve else 'N/A'}")
    
    # Check if the application has a room assignment
    has_assignment = False
    if application.status == 'approved':
        has_assignment = hasattr(application, 'room_assignment') and application.room_assignment is not None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            if not application.can_be_approved():
                messages.error(request, 'This application cannot be approved because it is not in pending status.')
                return redirect('hostel:manage_application', application_id=application.id)
            
            if not can_approve:
                messages.error(request, f'Cannot approve this application: {approval_blocked_reason}')
                return redirect('hostel:manage_application', application_id=application.id)
            
            # Check for available room of requested type and period
            from .models import Room
            available_rooms = Room.objects.filter(
                room_type=application.room_type,
                status='available'
            )
            available = False
            for room in available_rooms:
                if not room.is_full_for_period(application.start_date, application.end_date):
                    available = True
                    break
            if not available:
                application.status = 'rejected'
                application.rejection_reason = 'No available room for requested type'
                application.is_auto_rejected = True
                application.save()
                messages.error(request, 'No available room for requested type. Application auto-rejected.')
                return redirect('hostel:all_applications')
            # Check quota
            if application.room_type == 'single' and approved_single >= quota_single:
                application.status = 'rejected'
                application.rejection_reason = 'Quota reached'
                application.is_auto_rejected = True
                application.save()
                messages.error(request, 'Quota for single rooms reached. Application auto-rejected.')
            elif application.room_type == 'double' and approved_double >= quota_double:
                application.status = 'rejected'
                application.rejection_reason = 'Quota reached'
                application.is_auto_rejected = True
                application.save()
                messages.error(request, 'Quota for double rooms reached. Application auto-rejected.')
            else:
                application.approve()
                application.is_auto_rejected = False
                application.rejection_reason = ''
                application.save()
                messages.success(request, 'Application approved successfully!')
                # After approval, check if quota is now full and auto-reject remaining pending
                if application.room_type == 'single' and approved_single + 1 >= quota_single:
                    HostelApplication.objects.filter(
                        semester=semester, room_type='single', status='pending'
                    ).update(status='rejected', rejection_reason='Quota reached', is_auto_rejected=True)
                if application.room_type == 'double' and approved_double + 1 >= quota_double:
                    HostelApplication.objects.filter(
                        semester=semester, room_type='double', status='pending'
                    ).update(status='rejected', rejection_reason='Quota reached', is_auto_rejected=True)
                return redirect('hostel:all_applications')
        elif action == 'reject' and application.can_be_rejected():
            # If this was an approved application, we need to free up quota
            was_approved = application.status == 'approved'
            
            # If the application was approved and has a room assignment, release the room
            if was_approved and hasattr(application, 'room_assignment') and application.room_assignment:
                # Get the room assignment
                room_assignment = application.room_assignment
                
                # Delete any associated payments
                Payment.objects.filter(room_assignment=room_assignment).delete()
                
                # Mark the room assignment as cancelled
                room_assignment.status = 'cancelled'
                room_assignment.save()
                
                # Log the action
                print(f"DEBUG: Room {room_assignment.room.room_number} released after application {application.id} was rejected")
            
            application.reject()
            application.rejection_reason = request.POST.get('rejection_reason', 'Rejected by staff')
            application.save()
            messages.success(request, 'Application rejected successfully!')
            
            # If this was previously approved, try to reinstate oldest auto-rejected
            if was_approved:
                # Find oldest auto-rejected for this room type
                quota = quota_single if application.room_type == 'single' else quota_double
                approved_count = HostelApplication.objects.filter(semester=semester, room_type=application.room_type, status='approved').count()
                if approved_count < quota:
                    reinstates = HostelApplication.objects.filter(
                        semester=semester, room_type=application.room_type, status='rejected', is_auto_rejected=True
                    ).order_by('date_applied')[:quota - approved_count]
                    for app in reinstates:
                        app.status = 'pending'
                        app.is_auto_rejected = False
                        app.rejection_reason = ''
                        app.save()
        else:
            messages.error(request, 'Invalid action or application cannot be updated.')
        return redirect('hostel:all_applications')
    
    context = {
        'application': application,
        'special_requests': application.special_requests,
        'quota_single': quota_single,
        'quota_double': quota_double,
        'approved_single': approved_single,
        'approved_double': approved_double,
        'remaining_single': remaining_single,
        'remaining_double': remaining_double,
        'available_single_rooms': available_single_rooms,
        'available_double_rooms': available_double_rooms,
        'can_approve': can_approve,
        'approval_blocked_reason': approval_blocked_reason,
        'has_assignment': has_assignment,
    }
    
    return render(request, 'hostel/manage_application.html', context)

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def all_applications(request):
    semester_id = request.GET.get('semester')
    applications = HostelApplication.objects.all().order_by('date_applied')
    if semester_id:
        applications = applications.filter(semester_id=semester_id)
    semesters = Semester.objects.all().order_by('-id')
    
    # Auto-reject applications when quota is reached or no rooms available
    pending_applications = applications.filter(status='pending')
    for semester in Semester.objects.filter(id__in=pending_applications.values_list('semester', flat=True).distinct()):
        # Check quotas for this semester
        approved_single = HostelApplication.objects.filter(semester=semester, room_type='single', status='approved').count()
        approved_double = HostelApplication.objects.filter(semester=semester, room_type='double', status='approved').count()
        quota_single = semester.quota_single
        quota_double = semester.quota_double * 2  # double room quota is number of students
        
        # Auto-reject if quota reached
        if approved_single >= quota_single:
            HostelApplication.objects.filter(
                semester=semester, room_type='single', status='pending'
            ).update(status='rejected', rejection_reason='Quota reached', is_auto_rejected=True)
            
        if approved_double >= quota_double:
            HostelApplication.objects.filter(
                semester=semester, room_type='double', status='pending'
            ).update(status='rejected', rejection_reason='Quota reached', is_auto_rejected=True)
    
    # Refresh applications list after auto-rejections
    applications = HostelApplication.objects.all().order_by('date_applied')
    if semester_id:
        applications = applications.filter(semester_id=semester_id)
    
    app_list = []
    for app in applications:
        has_assignment = False
        if app.status == 'approved':
            # Check if this specific application has a room assignment
            try:
                has_assignment = hasattr(app, 'room_assignment') and app.room_assignment is not None
            except:
                # Fallback to checking if there's any assignment linked to this application
                has_assignment = RoomAssignment.objects.filter(hostel_application=app).exists()
        app_list.append({
            'app': app,
            'has_assignment': has_assignment,
        })
    return render(request, 'hostel/all_applications.html', {
        'applications': app_list,
        'user': request.user,
        'semesters': semesters,
        'selected_semester': int(semester_id) if semester_id else None
    })

# Staff: List all semesters
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def list_semesters(request):
    semesters = Semester.objects.all().order_by('-id')
    return render(request, 'hostel/semesters_list.html', {'semesters': semesters})

# Staff: Add a new semester
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def add_semester(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save(commit=False)
            
            # Combine date and time fields for application_start
            app_start_date = form.cleaned_data['application_start']
            app_start_time = form.cleaned_data['application_start_time']
            naive_datetime = datetime.datetime.combine(app_start_date, app_start_time)
            semester.application_start = timezone.make_aware(naive_datetime)
            
            # Combine date and time fields for application_end
            app_end_date = form.cleaned_data['application_end']
            app_end_time = form.cleaned_data['application_end_time']
            naive_datetime = datetime.datetime.combine(app_end_date, app_end_time)
            semester.application_end = timezone.make_aware(naive_datetime)
            
            semester.save()
            messages.success(request, 'Semester added successfully!')
            return redirect('hostel:list_semesters')
    else:
        form = SemesterForm()
    return render(request, 'hostel/semester_form.html', {'form': form, 'action': 'Add'})

# Staff: Edit a semester
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def edit_semester(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Extract time components for the form - convert to local time first
    local_app_start = timezone.localtime(semester.application_start)
    local_app_end = timezone.localtime(semester.application_end)
    
    initial_data = {
        'application_start_time': local_app_start.time(),
        'application_end_time': local_app_end.time(),
    }
    
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            semester = form.save(commit=False)
            
            # Combine date and time fields for application_start
            app_start_date = form.cleaned_data['application_start']
            app_start_time = form.cleaned_data['application_start_time']
            naive_datetime = datetime.datetime.combine(app_start_date, app_start_time)
            semester.application_start = timezone.make_aware(naive_datetime)
            
            # Combine date and time fields for application_end
            app_end_date = form.cleaned_data['application_end']
            app_end_time = form.cleaned_data['application_end_time']
            naive_datetime = datetime.datetime.combine(app_end_date, app_end_time)
            semester.application_end = timezone.make_aware(naive_datetime)
            
            semester.save()
            messages.success(request, 'Semester updated successfully!')
            return redirect('hostel:list_semesters')
    else:
        form = SemesterForm(instance=semester, initial=initial_data)
    return render(request, 'hostel/semester_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def delete_semester(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id)
    from .models import HostelApplication
    has_applications = HostelApplication.objects.filter(semester=semester).exists()
    if request.method == 'POST':
        if has_applications:
            messages.error(request, 'Cannot delete this semester because there are hostel applications associated with it.')
            return redirect('hostel:list_semesters')
        else:
            semester.is_active = False
            semester.save()
            messages.success(request, 'Semester deactivated (soft deleted) successfully!')
            return redirect('hostel:list_semesters')
    return render(request, 'hostel/semester_confirm_delete.html', {'semester': semester, 'has_applications': has_applications})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def assign_room(request, application_id):
    application = get_object_or_404(HostelApplication, id=application_id)
    
    # Check if application is approved
    if application.status != 'approved':
        messages.error(request, 'Room can only be assigned to approved applications.')
        return redirect('hostel:all_applications')
    
    # Check if student already has an active room assignment
    already_assigned = RoomAssignment.objects.filter(
        student=application.student, 
        status='active', 
        start_date__lte=timezone.now().date(), 
        end_date__gte=timezone.now().date()
    ).exists()
    
    if already_assigned:
        messages.warning(request, 'This student already has an active room assignment.')
        return redirect('hostel:all_applications')
    
    start_date = application.start_date
    end_date = application.end_date
    
    if request.method == 'POST':
        form = RoomAssignmentForm(request.POST, start_date=start_date, end_date=end_date, application=application)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.student = application.student
            assignment.start_date = start_date
            assignment.end_date = end_date
            assignment.hostel_application = application
            assignment.save()

            # Create a payment record for the assignment
            # Recalculate price based on actual assignment duration
            days = (assignment.end_date - assignment.start_date).days + 1
            price_per_day = get_room_price(
                 assignment.student.student_type,
                 assignment.room.room_type,
                 assignment.hostel_application.semester.name # Use semester from linked application
            ) / 119 # Divide by default semester length to get price per day
            total_price = price_per_day * days

            Payment.objects.create(
                student=assignment.student,
                room_assignment=assignment,
                amount=total_price,
                payment_period_start=assignment.start_date,
                payment_period_end=assignment.end_date,
                payment_method='cash', # Only support cash payments at counter
                status='pending'
            )

            # Update room status if now full for the period
            if assignment.room.is_full_for_period(start_date, end_date):
                assignment.room.status = 'occupied'
            else:
                assignment.room.status = 'available'
            assignment.room.save()
            messages.success(request, f'Room {assignment.room.room_number} assigned to {application.student.get_full_name()} successfully!')
            return redirect('hostel:all_applications')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = RoomAssignmentForm(start_date=start_date, end_date=end_date, application=application)
    return render(request, 'hostel/assign_room.html', {'form': form, 'application': application})

@login_required
def my_room(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view room assignments.')
        return redirect('accounts:dashboard')

    # Find the latest approved application with a room assignment
    assignment = RoomAssignment.objects.filter(
        student=request.user,
        hostel_application__status='approved'
    ).order_by('-date_assigned').first()

    roommates = []
    payment = None
    if assignment:
        # Find roommates (other students in the same room and period)
        roommates = RoomAssignment.objects.filter(
            room=assignment.room,
            status='active',
            start_date=assignment.start_date,
            end_date=assignment.end_date
        ).exclude(student=request.user)
        # Get payment for this assignment
        payment = assignment.payments.first()

    return render(request, 'hostel/my_room.html', {
        'assignment': assignment,
        'roommates': roommates,
        'payment': payment,
    })

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def delete_application(request, application_id):
    application = get_object_or_404(HostelApplication, id=application_id)
    if application.status == 'approved':
        messages.error(request, 'You cannot delete an approved application.')
        return redirect('hostel:all_applications')
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Hostel application deleted successfully.')
        return redirect('hostel:all_applications')
    return render(request, 'hostel/application_confirm_delete.html', {'application': application})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def list_rooms(request):
    rooms = Room.objects.all().order_by('room_number')
    return render(request, 'hostel/rooms_list.html', {'rooms': rooms})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def add_room(request):
    RoomForm = modelform_factory(Room, fields=['room_number', 'room_type', 'status'])
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room added successfully!')
            return redirect('hostel:list_rooms')
    else:
        form = RoomForm()
    return render(request, 'hostel/room_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    RoomForm = modelform_factory(Room, fields=['room_number', 'room_type', 'status'])
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('hostel:list_rooms')
    else:
        form = RoomForm(instance=room)
    return render(request, 'hostel/room_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully!')
        return redirect('hostel:list_rooms')
    return render(request, 'hostel/room_confirm_delete.html', {'room': room})

@login_required
def my_payments(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view payment history.')
        return redirect('accounts:dashboard')

    payments = Payment.objects.filter(student=request.user).select_related('room_assignment__hostel_application__semester').order_by('-payment_period_start')
    # Group by semester
    payments_by_semester = {}
    for payment in payments:
        semester = payment.room_assignment.hostel_application.semester if payment.room_assignment and payment.room_assignment.hostel_application else None
        if semester:
            payments_by_semester.setdefault(semester, []).append(payment)
    # Payment status summary
    pending_count = payments.filter(status='pending').count()
    completed_count = payments.filter(status='completed').count()
    refunded_count = payments.filter(status='refunded').count()
    total_count = payments.count()
    return render(request, 'hostel/student/my_payments.html', {
        'payments_by_semester': payments_by_semester,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'refunded_count': refunded_count,
        'total_count': total_count,
    })

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def approve_application(request, application_id):
    """Direct approval view that doesn't rely on form submission"""
    application = get_object_or_404(HostelApplication, id=application_id)
    semester = application.semester
    
    # Check if application can be approved
    if application.status != 'pending':
        messages.error(request, 'Only pending applications can be approved.')
        return redirect('hostel:all_applications')
    
    # Count approved applications for this semester and room type
    approved_single = HostelApplication.objects.filter(semester=semester, room_type='single', status='approved').count()
    approved_double = HostelApplication.objects.filter(semester=semester, room_type='double', status='approved').count()
    quota_single = semester.quota_single
    quota_double = semester.quota_double * 2  # double room quota is number of students
    
    # Check quota
    if application.room_type == 'single' and approved_single >= quota_single:
        application.status = 'rejected'
        application.rejection_reason = 'Quota reached'
        application.is_auto_rejected = True
        application.save()
        messages.error(request, 'Quota for single rooms reached. Application auto-rejected.')
        return redirect('hostel:all_applications')
    elif application.room_type == 'double' and approved_double >= quota_double:
        application.status = 'rejected'
        application.rejection_reason = 'Quota reached'
        application.is_auto_rejected = True
        application.save()
        messages.error(request, 'Quota for double rooms reached. Application auto-rejected.')
        return redirect('hostel:all_applications')
    
    # Check for available room of requested type and period
    from .models import Room
    available_rooms = Room.objects.filter(
        room_type=application.room_type,
        status='available'
    )
    
    # Count available rooms/spots for the requested period
    available_spots = 0
    for room in available_rooms:
        if not room.is_full_for_period(application.start_date, application.end_date):
            if application.room_type == 'single':
                available_spots += 1
            else:  # double room
                # For double rooms, count available spots (could be 1 or 2 per room)
                capacity = room.capacity
                current_occupants = room.assignments.filter(
                    status='active',
                    start_date__lt=application.end_date,
                    end_date__gt=application.start_date
                ).count()
                available_spots += (capacity - current_occupants)
    
    # If no spots available, auto-reject
    if available_spots <= 0:
        application.status = 'rejected'
        application.rejection_reason = f'No available {application.get_room_type_display().lower()} for the requested period'
        application.is_auto_rejected = True
        application.save()
        messages.error(request, f'No available {application.get_room_type_display().lower()} for the requested period. Application auto-rejected.')
        return redirect('hostel:all_applications')
    
    # All checks passed, approve the application
    application.status = 'approved'
    application.is_auto_rejected = False
    application.rejection_reason = ''
    application.save()
    messages.success(request, 'Application approved successfully!')
    
    # After approval, check if quota is now full and auto-reject remaining pending
    if application.room_type == 'single' and approved_single + 1 >= quota_single:
        HostelApplication.objects.filter(
            semester=semester, room_type='single', status='pending'
        ).update(status='rejected', rejection_reason='Quota reached', is_auto_rejected=True)
    if application.room_type == 'double' and approved_double + 1 >= quota_double:
        HostelApplication.objects.filter(
            semester=semester, room_type='double', status='pending'
        ).update(status='rejected', rejection_reason='Quota reached', is_auto_rejected=True)
    
    return redirect('hostel:all_applications')

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def update_room_statuses(request):
    """
    Manually update all room statuses based on current assignments
    """
    from .models import Room
    rooms = Room.objects.all()
    updated_count = 0
    
    for room in rooms:
        old_status = room.status
        room.update_status()
        if old_status != room.status:
            updated_count += 1
    
    if updated_count > 0:
        messages.success(request, f'Successfully updated {updated_count} room statuses.')
    else:
        messages.info(request, 'All room statuses are already up to date.')
    
    return redirect('hostel:list_rooms')

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def manage_payments(request):
    """View for staff to manage student payments"""
    status = request.GET.get('status')
    semester_id = request.GET.get('semester')
    
    # Get only payments for students with approved applications and assigned rooms
    payments = Payment.objects.filter(
        room_assignment__isnull=False,  # Has a room assignment
        room_assignment__hostel_application__status='approved'  # Application is approved
    ).select_related(
        'student', 
        'room_assignment__room',
        'room_assignment__hostel_application__semester'
    ).order_by('-payment_period_start')
    
    # Apply filters if provided
    if status:
        payments = payments.filter(status=status)
    
    if semester_id:
        payments = payments.filter(room_assignment__hostel_application__semester_id=semester_id)
    
    # Get all semesters for filter dropdown
    semesters = Semester.objects.all().order_by('-start_date')
    
    return render(request, 'hostel/staff/manage_payments.html', {
        'payments': payments,
        'semesters': semesters,
        'status': status,
        'semester': semester_id,
    })

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def update_payment_status(request, payment_id):
    """View for staff to update payment status"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('hostel:manage_payments')
    
    payment = get_object_or_404(Payment, id=payment_id)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Payment.STATUS_CHOICES):
        messages.error(request, 'Invalid payment status.')
        return redirect('hostel:manage_payments')
    
    # Update payment status
    payment.status = new_status
    
    # If marking as completed, set the date_paid to now
    if new_status == 'completed':
        payment.date_paid = timezone.now()
    
    payment.save()
    
    # Update the room assignment payment status if this is the only payment
    if new_status == 'completed':
        room_assignment = payment.room_assignment
        room_assignment.payment_status = 'paid'
        room_assignment.save()
    
    messages.success(request, f'Payment status updated to {payment.get_status_display()}.')
    return redirect('hostel:manage_payments')

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def room_statistics(request):
    """View for staff to see room statistics and reports"""
    # Get all rooms
    all_rooms = Room.objects.all()
    
    # Count rooms by type
    single_rooms = all_rooms.filter(room_type='single').count()
    double_rooms = all_rooms.filter(room_type='double').count()
    
    # Calculate total capacity
    total_single_capacity = single_rooms
    total_double_capacity = double_rooms * 2  # Each double room can accommodate 2 students
    
    # Count current occupancy
    active_assignments = RoomAssignment.objects.filter(status='active')
    
    # Get current date
    today = timezone.now().date()
    
    # Count current occupancy (assignments that include today's date)
    current_single_occupancy = active_assignments.filter(
        room__room_type='single',
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    current_double_occupancy = active_assignments.filter(
        room__room_type='double',
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    # Calculate available spots
    available_single = total_single_capacity - current_single_occupancy
    available_double = total_double_capacity - current_double_occupancy
    
    # Calculate occupancy rates
    single_occupancy_rate = 0
    if total_single_capacity > 0:
        single_occupancy_rate = round((current_single_occupancy / total_single_capacity) * 100)
    
    double_occupancy_rate = 0
    if total_double_capacity > 0:
        double_occupancy_rate = round((current_double_occupancy / total_double_capacity) * 100)
    
    # Get room preference statistics from applications
    all_applications = HostelApplication.objects.all()
    single_applications = all_applications.filter(room_type='single').count()
    double_applications = all_applications.filter(room_type='double').count()
    
    # Get active semester for quota information
    active_semesters = Semester.objects.filter(is_active=True)
    semester_data = []
    
    for semester in active_semesters:
        # Count approved applications for this semester
        approved_single = HostelApplication.objects.filter(
            semester=semester, 
            room_type='single', 
            status='approved'
        ).count()
        
        approved_double = HostelApplication.objects.filter(
            semester=semester, 
            room_type='double', 
            status='approved'
        ).count()
        
        # Calculate remaining quota
        remaining_single_quota = max(0, semester.quota_single - approved_single)
        remaining_double_quota = max(0, semester.quota_double * 2 - approved_double)
        
        semester_data.append({
            'name': semester.name,
            'quota_single': semester.quota_single,
            'quota_double': semester.quota_double * 2,  # Convert to student capacity
            'approved_single': approved_single,
            'approved_double': approved_double,
            'remaining_single_quota': remaining_single_quota,
            'remaining_double_quota': remaining_double_quota
        })
    
    # Calculate monthly statistics for the past year
    one_year_ago = timezone.now() - datetime.timedelta(days=365)
    monthly_applications = HostelApplication.objects.filter(
        date_applied__gte=one_year_ago
    ).extra(
        select={'month': "EXTRACT(month FROM date_applied)"}
    ).values('month', 'room_type').annotate(count=Count('id')).order_by('month')
    
    # Format data for charts
    months = list(range(1, 13))
    monthly_data = {
        'single': [0] * 12,
        'double': [0] * 12
    }
    
    for item in monthly_applications:
        month_index = int(item['month']) - 1  # Convert to 0-based index
        room_type = item['room_type']
        count = item['count']
        monthly_data[room_type][month_index] = count
    
    # Ensure all values are at least 0 (not None) for the charts
    context = {
        'single_rooms': single_rooms or 0,
        'double_rooms': double_rooms or 0,
        'total_single_capacity': total_single_capacity or 0,
        'total_double_capacity': total_double_capacity or 0,
        'current_single_occupancy': current_single_occupancy or 0,
        'current_double_occupancy': current_double_occupancy or 0,
        'available_single': available_single or 0,
        'available_double': available_double or 0,
        'single_applications': single_applications or 0,
        'double_applications': double_applications or 0,
        'single_occupancy_rate': single_occupancy_rate,
        'double_occupancy_rate': double_occupancy_rate,
        'semester_data': semester_data,
        'monthly_data': monthly_data,
        'months': months
    }
    
    # Add dummy data if no rooms exist to ensure charts render
    if single_rooms == 0 and double_rooms == 0:
        context.update({
            'single_rooms': 1,
            'double_rooms': 1,
            'total_single_capacity': 1,
            'total_double_capacity': 2,
            'current_single_occupancy': 0,
            'current_double_occupancy': 0,
            'available_single': 1,
            'available_double': 2,
        })
    
    return render(request, 'hostel/staff/room_statistics.html', context)
