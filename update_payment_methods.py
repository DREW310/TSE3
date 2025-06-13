import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from apps.hostel.models import Payment

def update_payment_methods():
    # Update all existing payment methods from 'tng' to 'cash'
    updated_count = Payment.objects.filter(payment_method='tng').update(payment_method='cash')
    print(f"Updated {updated_count} payment records from 'tng' to 'cash'.")

if __name__ == '__main__':
    update_payment_methods() 