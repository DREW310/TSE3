from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.accounts.models import User

User = get_user_model()

# Create your models here.

# Model to store semester info
class Semester(models.Model):
    name = models.CharField(max_length=30, unique=True)  # e.g., "2023/2024, Trimester 1"
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    application_start = models.DateTimeField(default=timezone.now)
    application_end = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_application_open(self):
        """Check if applications are currently open for this semester"""
        now = timezone.now()
        return (
            self.is_active and 
            self.application_start <= now <= self.application_end
        )
        
    def is_application_future(self):
        """Check if applications will open in the future"""
        now = timezone.now()
        return self.application_start > now
        
    def is_application_closed(self):
        """Check if applications are closed"""
        now = timezone.now()
        return now > self.application_end

# Model to store hostel applications submitted by students
class HostelApplication(models.Model):
    # Link each application to a student user
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hostel_applications')

    # Room type choices (single, double only)
    ROOM_TYPE_CHOICES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
    ]
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES)

    # Semester for which the application is made (FK to Semester)
    semester = models.ForeignKey('Semester', on_delete=models.PROTECT)

    # Application status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Date and time when the application was submitted
    date_applied = models.DateTimeField(auto_now_add=True)

    # Start date of the student's requested stay
    start_date = models.DateField(default='2024-06-01')

    # End date of the student's requested stay
    end_date = models.DateField(default='2024-06-30')

    def __str__(self):
        # This will show up in the admin panel and makes it easy to identify applications
        return f"{self.student.username} - {self.room_type} ({self.start_date} to {self.end_date})"

    def can_be_approved(self):
        return self.status == 'pending'

    def approve(self):
        if self.can_be_approved():
            self.status = 'approved'
            self.save()
            return True
        return False

    def reject(self):
        if self.can_be_approved():
            self.status = 'rejected'
            self.save()
            return True
        return False

# Model to store rooms in the hostel
class Room(models.Model):
    # Room number (e.g., A101)
    room_number = models.CharField(max_length=10, unique=True)

    # Room type choices
    ROOM_TYPE_CHOICES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
    ]
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES)

    # Room status
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')

    # Room features
    # (Fields removed as requested)

    @property
    def capacity(self):
        if self.room_type == 'single':
            return 1
        elif self.room_type == 'double':
            return 2
        else:
            return 1  # Default fallback

    def __str__(self):
        return f"Room {self.room_number}"

    def is_available(self):
        return self.status == 'available'

    def get_current_occupants(self):
        # This method is for getting occupants currently in the room based on date
        return self.assignments.filter(
            status='active',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )

    def get_occupancy_count(self):
        # This method will now count all assignments that are not cancelled
        return self.assignments.exclude(status='cancelled').count()

    def can_accommodate_more(self):
        return self.get_occupancy_count() < self.capacity

    def is_full_for_period(self, start_date, end_date):
        overlapping = self.assignments.filter(
            status='active',
            start_date__lt=end_date,
            end_date__gt=start_date
        ).count()
        return overlapping >= self.capacity

# Model to store room assignments
class RoomAssignment(models.Model):
    # Link to the student
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_assignments')

    # Link to the room
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='assignments')

    # Link to the hostel application that led to this assignment
    hostel_application = models.OneToOneField(HostelApplication, on_delete=models.SET_NULL, null=True, blank=True, related_name='room_assignment')

    # Assignment period
    start_date = models.DateField()
    end_date = models.DateField()

    # Assignment status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Payment status
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Date and time when the assignment was created
    date_assigned = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - Room {self.room.room_number}"

    def is_active(self):
        return self.status == 'active' and self.start_date <= timezone.now().date() <= self.end_date

    def can_be_cancelled(self):
        return self.status == 'active' and self.start_date > timezone.now().date()

# Model to store maintenance requests from students
class MaintenanceRequest(models.Model):
    # Link each request to a student user
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')

    # Request type choices
    REQUEST_TYPE_CHOICES = [
        ('electrical', 'Electrical Issue'),
        ('plumbing', 'Plumbing Issue'),
        ('furniture', 'Furniture Repair'),
        ('cleaning', 'Cleaning Request'),
        ('other', 'Other Issue'),
    ]
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)

    # Room number where the issue is located
    room_number = models.CharField(max_length=10)

    # Detailed description of the issue
    description = models.TextField()

    # Priority level of the request
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Request status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Date and time when the request was submitted
    date_submitted = models.DateTimeField(auto_now_add=True)

    # Date and time when the request was last updated
    last_updated = models.DateTimeField(auto_now=True)

    # Staff assigned to handle the request
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')

    # Staff notes/comments on the request
    staff_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.request_type}"

    def can_be_updated(self):
        return self.status not in ['completed', 'cancelled']

    def update_status(self, new_status, staff_notes=None):
        if self.can_be_updated() and new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            if staff_notes:
                self.staff_notes = staff_notes
            self.save()
            return True
        return False

# Model to store hostel fee payments
class Payment(models.Model):
    # Link to the student
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')

    # Link to the room assignment
    room_assignment = models.ForeignKey(RoomAssignment, on_delete=models.CASCADE, related_name='payments')

    # Payment amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment period
    payment_period_start = models.DateField()
    payment_period_end = models.DateField()

    # Payment method
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('tng', 'Touch \'n Go'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)

    # Payment status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Transaction reference (for TNG payments)
    transaction_reference = models.CharField(max_length=100, null=True, blank=True)

    # Date and time when the payment was made
    date_paid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - RM{self.amount}"

    def is_payment_period_valid(self):
        return self.payment_period_start <= timezone.now().date() <= self.payment_period_end

    def can_be_refunded(self):
        return self.status == 'completed' and self.date_paid >= timezone.now() - timezone.timedelta(days=7)

    def process_payment(self, transaction_ref=None):
        if self.status == 'pending':
            self.status = 'completed'
            if transaction_ref:
                self.transaction_reference = transaction_ref
            self.save()
            return True
        return False

# Helper function to get room price based on student type, room type, and semester
# You can call this from your views or templates
# Example rates (replace with your actual rates)
def get_room_price(student_type, room_type, semester_name):
    """
    Returns the total room price (in RM) for a student based on their type, room type, and semester.
    Rates are per day.
    - Local: Single RM 15/day, Double RM 10/day
    - International: Single RM 25/day, Double RM 16/day
    Trimester 1 & 2: 119 days (17 weeks)
    Trimester 3: 63 days (9 weeks)
    """
    rates = {
        'local': {'single': 15, 'double': 10},
        'international': {'single': 25, 'double': 16},
    }
    if 'Trimester 3' in semester_name:
        days = 63
    else:
        days = 119
    return rates[student_type][room_type] * days
