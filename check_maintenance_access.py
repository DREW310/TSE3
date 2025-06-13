import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from apps.hostel.models import RoomAssignment, Payment, MaintenanceRequest
from apps.accounts.models import User
from django.utils import timezone

def check_maintenance_access():
    # Find Yi Xuan Kong's user
    try:
        user = User.objects.get(student_id='1211109458')
        print(f"Found user: {user.get_full_name()} (ID: {user.student_id})")
        
        # Check if student has an active room assignment
        active_assignment = RoomAssignment.objects.filter(
            student=user,
            status='active',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).first()
        
        if active_assignment:
            print(f"Active room assignment found: {active_assignment}")
            print(f"Room: {active_assignment.room.room_number}")
            print(f"Status: {active_assignment.status}")
            print(f"Payment status: {active_assignment.payment_status}")
            print(f"Period: {active_assignment.start_date} to {active_assignment.end_date}")
            
            # Check if payment for this assignment is completed
            payment = active_assignment.payments.filter(status='completed').first()
            if payment:
                print(f"Payment found with status: {payment.status}")
                print("Student should be able to submit maintenance requests")
            else:
                print("No completed payment found - student cannot submit maintenance requests")
                payments = active_assignment.payments.all()
                for p in payments:
                    print(f"  Payment ID: {p.id}, Status: {p.status}")
        else:
            print("No active room assignment found - student cannot submit maintenance requests")
        
        # Check existing maintenance requests
        maintenance_requests = MaintenanceRequest.objects.filter(student=user)
        print(f"\nExisting maintenance requests: {maintenance_requests.count()}")
        for req in maintenance_requests:
            print(f"  Request ID: {req.id}")
            print(f"  Type: {req.request_type}")
            print(f"  Status: {req.status}")
            print(f"  Submitted: {req.date_submitted}")
            print("  ---")
    
    except User.DoesNotExist:
        print("User not found")

if __name__ == '__main__':
    check_maintenance_access() 