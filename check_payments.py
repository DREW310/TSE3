import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from apps.hostel.models import Payment, RoomAssignment, HostelApplication

def check_payments():
    # Get all payments
    payments = Payment.objects.all().select_related(
        'student', 
        'room_assignment',
        'room_assignment__hostel_application'
    )
    
    print(f"Total payments: {payments.count()}")
    
    for payment in payments:
        student_name = payment.student.get_full_name() or payment.student.username
        room_number = payment.room_assignment.room.room_number if payment.room_assignment and payment.room_assignment.room else "No room"
        application_status = payment.room_assignment.hostel_application.status if payment.room_assignment and payment.room_assignment.hostel_application else "No application"
        
        print(f"Payment ID: {payment.id}")
        print(f"  Student: {student_name} (ID: {payment.student.student_id})")
        print(f"  Room: {room_number}")
        print(f"  Amount: RM{payment.amount}")
        print(f"  Status: {payment.status}")
        print(f"  Application Status: {application_status}")
        print("  ---")

if __name__ == '__main__':
    check_payments() 