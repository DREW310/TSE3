import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from apps.hostel.models import Payment, RoomAssignment, HostelApplication

def cleanup_payments():
    # Find payments associated with rejected applications
    invalid_payments = Payment.objects.filter(
        room_assignment__hostel_application__status='rejected'
    )
    
    count = invalid_payments.count()
    print(f"Found {count} payments associated with rejected applications")
    
    if count > 0:
        # Delete these payments
        invalid_payments.delete()
        print(f"Deleted {count} invalid payments")
    
    # Verify that all remaining payments are for approved applications
    remaining_payments = Payment.objects.all()
    print(f"Remaining payments: {remaining_payments.count()}")
    
    for payment in remaining_payments:
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
    cleanup_payments() 