from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.hostel.models import RoomAssignment

class Command(BaseCommand):
    help = 'Check for expired room assignments and mark them as completed'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking for expired room assignments...'))
        
        # Call the class method to check and update expired assignments
        count = RoomAssignment.check_expired_assignments()
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {count} expired assignment(s) as completed'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired assignments found')) 