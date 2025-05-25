from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import HostelApplicationForm, MaintenanceRequestForm, RoomAssignmentForm
from .models import HostelApplication, MaintenanceRequest, Room, RoomAssignment, Semester, get_room_price, Payment
from django import forms
from datetime import date
from django.forms import modelform_factory

# Create your views here.

# View for students to apply for hostel accommodation
@login_required
def apply_for_hostel(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can apply for hostel accommodation.')
        return redirect('accounts:dashboard')

    available_semesters = Semester.objects.filter(is_active=True)
    already_applied = HostelApplication.objects.filter(
        student=request.user,
        status__in=['pending', 'approved']
    ).exists()

    if request.method == 'POST':
        form = HostelApplicationForm(request.POST)
        if already_applied:
            messages.warning(request, 'You already have a pending or approved hostel application.')
        elif form.is_valid():
            application = form.save(commit=False)
            application.student = request.user
            application.save()
            # Calculate price based on actual duration
            days = (application.end_date - application.start_date).days + 1
            price = get_room_price(
                request.user.student_type,
                application.room_type,
                application.semester.name
            )
            price = int(price / 119 * days) if days > 0 else 0  # 119 is the default semester length
            return render(request, 'hostel/application_confirmation.html', {
                'application': application,
                'user': request.user,
                'price': price,
            })
        else:
            messages.error(request, 'Please correct the errors in your application.')
    else:
        form = HostelApplicationForm()

    return render(request, 'hostel/apply.html', {
        'form': form,
        'already_applied': already_applied,
    })

# View for students to see their hostel application status
@login_required
def my_hostel_application(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view hostel applications.')
        return redirect('accounts:dashboard')

    application = HostelApplication.objects.filter(student=request.user).order_by('-date_applied').first()
    semester_name = application.semester.name if application else None
    return render(request, 'hostel/my_application.html', {'application': application, 'semester_name': semester_name})

# View for students to submit a maintenance request
@login_required
def submit_maintenance_request(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can submit maintenance requests.')
        return redirect('accounts:dashboard')

    # Check if student has an active room assignment
    active_assignment = RoomAssignment.objects.filter(
        student=request.user,
        status='active',
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).first()
    
    if not active_assignment:
        messages.error(request, 'You must have an active room assignment to submit maintenance requests.')
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

    requests = MaintenanceRequest.objects.filter(
        student=request.user
    ).order_by('-date_submitted')
    
    return render(request, 'hostel/my_maintenance_requests.html', {'requests': requests})

# View for staff to see all maintenance requests
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def all_maintenance_requests(request):
    requests = MaintenanceRequest.objects.all().order_by('-date_submitted')
    return render(request, 'hostel/all_maintenance_requests.html', {'requests': requests})

# View for staff to manage a specific maintenance request
@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def manage_maintenance_request(request, request_id):
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        staff_notes = request.POST.get('staff_notes')
        
        if status in dict(MaintenanceRequest.STATUS_CHOICES):
            if maintenance_request.update_status(status, staff_notes):
                messages.success(request, 'Maintenance request updated successfully!')
            else:
                messages.error(request, 'Cannot update this request.')
            return redirect('hostel:all_maintenance_requests')
        else:
            messages.error(request, 'Invalid status selected.')
    
    return render(request, 'hostel/manage_maintenance_request.html', {
        'maintenance_request': maintenance_request
    })

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def manage_application(request, application_id):
    application = get_object_or_404(HostelApplication, id=application_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve' and application.can_be_approved():
            application.approve()
            messages.success(request, 'Application approved successfully!')
        elif action == 'reject' and application.can_be_approved():
            application.reject()
            messages.success(request, 'Application rejected successfully!')
        else:
            messages.error(request, 'Invalid action or application cannot be updated.')
        return redirect('hostel:all_applications')
    return render(request, 'hostel/manage_application.html', {'application': application})

@login_required
@user_passes_test(lambda u: u.user_type in ['staff', 'admin'])
def all_applications(request):
    applications = HostelApplication.objects.all().order_by('-date_applied')
    today = date.today()
    app_list = []
    for app in applications:
        has_assignment = False
        if app.status == 'approved':
            has_assignment = app.student.room_assignments.filter().exists()

        app_list.append({
            'app': app,
            'has_assignment': has_assignment,
        })
    return render(request, 'hostel/all_applications.html', {'applications': app_list, 'user': request.user})

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
    class SemesterForm(forms.ModelForm):
        class Meta:
            model = Semester
            fields = ['name', 'is_active']
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            form.save()
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
    class SemesterForm(forms.ModelForm):
        class Meta:
            model = Semester
            fields = ['name', 'is_active']
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester updated successfully!')
            return redirect('hostel:list_semesters')
    else:
        form = SemesterForm(instance=semester)
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
    already_assigned = RoomAssignment.objects.filter(student=application.student, status='active', start_date__lte=timezone.now().date(), end_date__gte=timezone.now().date()).exists()
    if application.status != 'approved':
        messages.error(request, 'Room can only be assigned to approved applications.')
        return redirect('hostel:all_applications')
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
                payment_method='tng', # Or a default method
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

    # The rest of the logic in the template will handle displaying details if an assignment is found
    return render(request, 'hostel/my_room.html', {'assignment': assignment})

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
