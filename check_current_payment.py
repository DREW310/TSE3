import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from apps.hostel.models import Payment, RoomAssignment
from apps.accounts.models import User

def check_payments():
    # Find Yi Xuan Kong's user
    try:
        user = User.objects.get(student_id='1211109458')
        print(f"Found user: {user.get_full_name()} (ID: {user.student_id})")
        
        # Find their room assignment
        room_assignments = RoomAssignment.objects.filter(student=user)
        print(f"Room assignments: {room_assignments.count()}")
        
        for assignment in room_assignments:
            print(f"Room: {assignment.room.room_number}")
            print(f"Status: {assignment.status}")
            print(f"Payment status: {assignment.payment_status}")
            print(f"Period: {assignment.start_date} to {assignment.end_date}")
            
            # Find payments for this assignment
            payments = Payment.objects.filter(room_assignment=assignment)
            print(f"Payments: {payments.count()}")
            
            for payment in payments:
                print(f"  Payment ID: {payment.id}")
                print(f"  Amount: RM{payment.amount}")
                print(f"  Status: {payment.status}")
                print(f"  Method: {payment.payment_method}")
                print(f"  Date paid: {payment.date_paid}")
                print("  ---")
    
    except User.DoesNotExist:
        print("User not found")

if __name__ == '__main__':
    check_payments() 