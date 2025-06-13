import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from apps.hostel.models import Payment

def check_payment_methods():
    # Check all payment methods in the database
    payments = Payment.objects.all()
    print(f"Total payments: {payments.count()}")
    
    # Count by payment method
    cash_count = payments.filter(payment_method='cash').count()
    tng_count = payments.filter(payment_method='tng').count()
    
    print(f"Cash payments: {cash_count}")
    print(f"TNG payments: {tng_count}")
    
    # List all payments with details
    print("\nPayment details:")
    for payment in payments:
        print(f"ID: {payment.id}, Student: {payment.student.username}, Method: {payment.payment_method}, Status: {payment.status}")

if __name__ == '__main__':
    check_payment_methods() 