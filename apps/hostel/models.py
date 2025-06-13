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
    quota_single = models.PositiveIntegerField(default=0, help_text="Quota for single rooms")
    quota_double = models.PositiveIntegerField(default=0, help_text="Quota for double rooms (number of rooms, not students)")

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
        ('single', 'Single Room (1 person per room)'),
        ('double', 'Double Room (2 persons per room)'),
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

    # Start and end dates (auto-set from semester)
    start_date = models.DateField()
    end_date = models.DateField()

    special_requests = models.TextField(blank=True, null=True, help_text="Any special requests by the student")
    rejection_reason = models.CharField(max_length=255, blank=True, null=True)
    is_auto_rejected = models.BooleanField(default=False, help_text="Auto-rejected due to quota reached")

    def __str__(self):
        return f"{self.student.username} - {self.room_type} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        # Auto-set start and end dates from semester
        if not self.start_date:
            self.start_date = self.semester.start_date
        if not self.end_date:
            self.end_date = self.semester.end_date
        super().save(*args, **kwargs)

    def get_daily_rate(self):
        """Get the daily rate based on student type and room type"""
        rates = {
            'local': {'single': 15, 'double': 10},
            'international': {'single': 25, 'double': 16}
        }
        student_type = self.student.student_type
        return rates.get(student_type, {}).get(self.room_type, 0)

    def get_stay_duration(self):
        """Get the number of days of stay"""
        if not self.start_date or not self.end_date:
            return 0
        return (self.end_date - self.start_date).days + 1

    def calculate_total_price(self):
        """Calculate the total price for the stay"""
        daily_rate = self.get_daily_rate()
        duration = self.get_stay_duration()
        return daily_rate * duration

    def can_be_approved(self):
        return self.status == 'pending'

    def can_be_rejected(self):
        # Both pending and approved applications can be rejected
        return self.status in ['pending', 'approved']

    def approve(self):
        if self.can_be_approved():
            self.status = 'approved'
            self.save()
            return True
        return False

    def reject(self):
        if self.can_be_rejected():
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
        # Debug print
        print(f"DEBUG: Checking if room {self.room_number} is full for period {start_date} to {end_date}")
        print(f"DEBUG: Room capacity: {self.capacity}")
        
        # Get overlapping assignments
        overlapping = self.assignments.filter(
            status='active',
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        # Debug print overlapping assignments
        print(f"DEBUG: Found {overlapping.count()} overlapping assignments")
        for assign in overlapping:
            print(f"DEBUG: Assignment for {assign.student} from {assign.start_date} to {assign.end_date}")
        
        # Room is full if number of overlapping assignments equals or exceeds capacity
        is_full = overlapping.count() >= self.capacity
        print(f"DEBUG: Room is full: {is_full}")
        
        return is_full

    def update_status(self):
        """Update room status based on all active assignments"""
        # First check if there are any current assignments (today falls within their period)
        today = timezone.now().date()
        current_assignments = self.assignments.filter(
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).count()
        
        # Also check if there are any active assignments regardless of date
        all_active_assignments = self.assignments.filter(status='active').count()
        
        if current_assignments == 0:
            if all_active_assignments > 0:
                # No current assignments but has future/past active assignments
                # Keep as occupied if it's already occupied
                if self.status == 'occupied':
                    return
                    
            # No current assignments and no need to keep as occupied
            if self.status != 'maintenance':  # Don't change if under maintenance
                self.status = 'available'
                self.save()
                print(f"DEBUG: Room {self.room_number} status updated to available")
        elif current_assignments >= self.capacity:
            # Room is at or over capacity with current assignments, mark as occupied
            self.status = 'occupied'
            self.save()
            print(f"DEBUG: Room {self.room_number} status updated to occupied")
        else:
            # Room has some current occupants but not full
            if self.room_type == 'single':
                # Single rooms are either occupied or available
                self.status = 'occupied'
                self.save()
            else:
                # Double rooms can be partially occupied but still available for more students
                self.status = 'available'
                self.save()
            print(f"DEBUG: Room {self.room_number} status updated to {self.status}")

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
        
    def save(self, *args, **kwargs):
        """Override save method to update room status"""
        super().save(*args, **kwargs)
        # Update room status after saving
        self.room.update_status()
        
    def cancel_assignment(self):
        """Cancel this assignment and update room status"""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            self.save()  # This will trigger room status update
            return True
        return False
        
    def mark_completed(self):
        """Mark this assignment as completed and update room status"""
        if self.status == 'active' and timezone.now().date() > self.end_date:
            self.status = 'completed'
            self.save()  # This will trigger room status update
            return True
        return False
    
    @classmethod
    def check_expired_assignments(cls):
        """
        Check for expired assignments and mark them as completed.
        This should be called daily via a scheduled task.
        """
        today = timezone.now().date()
        expired_assignments = cls.objects.filter(
            status='active',
            end_date__lt=today
        )
        
        count = 0
        for assignment in expired_assignments:
            if assignment.mark_completed():
                count += 1
                
        return count

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

    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_maintenance_requests')
    completed_at = models.DateTimeField(null=True, blank=True)

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

    def mark_completed(self, staff_user):
        self.status = 'completed'
        self.completed_by = staff_user
        self.completed_at = timezone.now()
        self.save()

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
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')

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
            
            # Update the room assignment payment status
            if self.room_assignment:
                self.room_assignment.payment_status = 'paid'
                self.room_assignment.save()
            
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
