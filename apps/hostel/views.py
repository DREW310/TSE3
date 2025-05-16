from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import HostelApplicationForm
from .models import HostelApplication

# Create your views here.

# View for students to apply for hostel accommodation
@login_required  # Only logged-in users can apply
def apply_for_hostel(request):
    # Check if the student already has an application
    existing_application = HostelApplication.objects.filter(student=request.user).first()
    if existing_application:
        # If already applied, redirect to status page
        messages.info(request, 'You have already applied for hostel accommodation.')
        return redirect('hostel:my_application')

    if request.method == 'POST':
        form = HostelApplicationForm(request.POST)
        if form.is_valid():
            # Create a new application but don't save yet
            application = form.save(commit=False)
            application.student = request.user  # Set the student to the logged-in user
            application.save()
            messages.success(request, 'Your hostel application has been submitted!')
            return redirect('hostel:my_application')
    else:
        form = HostelApplicationForm()

    return render(request, 'hostel/apply.html', {'form': form})

# View for students to see their hostel application status
@login_required
def my_hostel_application(request):
    # Get the student's application, if any
    application = HostelApplication.objects.filter(student=request.user).first()
    return render(request, 'hostel/my_application.html', {'application': application})
