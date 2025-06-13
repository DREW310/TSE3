import os
import django
import random
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from django.utils import timezone
from apps.hostel.models import Room, Semester, HostelApplication, RoomAssignment
from apps.accounts.models import User

def create_rooms():
    """Create sample rooms if none exist"""
    if Room.objects.count() == 0:
        print("Creating sample rooms...")
        
        # Create single rooms
        for i in range(1, 11):
            Room.objects.create(
                room_number=f"S{i:03d}",
                room_type="single",
                status="available"
            )
            
        # Create double rooms
        for i in range(1, 11):
            Room.objects.create(
                room_number=f"D{i:03d}",
                room_type="double",
                status="available"
            )
        
        print(f"Created {Room.objects.count()} rooms")
    else:
        print(f"Using existing {Room.objects.count()} rooms")

def create_semesters():
    """Create sample semesters if none exist"""
    if Semester.objects.count() == 0:
        print("Creating sample semesters...")
        
        # Current semester
        now = timezone.now()
        current_semester = Semester.objects.create(
            name="2023/2024, Trimester 2",
            start_date=now.date(),
            end_date=(now + timedelta(days=120)).date(),
            application_start=now - timedelta(days=30),
            application_end=now + timedelta(days=30),
            is_active=True,
            quota_single=15,
            quota_double=10
        )
        
        # Next semester
        next_semester = Semester.objects.create(
            name="2023/2024, Trimester 3",
            start_date=(now + timedelta(days=121)).date(),
            end_date=(now + timedelta(days=240)).date(),
            application_start=now + timedelta(days=60),
            application_end=now + timedelta(days=90),
            is_active=True,
            quota_single=15,
            quota_double=10
        )
        
        print(f"Created {Semester.objects.count()} semesters")
    else:
        print(f"Using existing {Semester.objects.count()} semesters")

def create_applications():
    """Create sample applications if few exist"""
    if HostelApplication.objects.count() < 10:
        print("Creating sample applications...")
        
        # Get students
        students = User.objects.filter(user_type='student')
        if not students:
            print("No student users found. Please create some students first.")
            return
        
        # Get semesters
        semesters = Semester.objects.filter(is_active=True)
        if not semesters:
            print("No active semesters found. Please create semesters first.")
            return
        
        current_semester = semesters.first()
        
        # Create applications with different room types
        room_types = ['single', 'double']
        statuses = ['pending', 'approved', 'rejected']
        
        # Create 20 random applications
        for i in range(20):
            student = random.choice(students)
            room_type = random.choice(room_types)
            status = random.choice(statuses)
            
            # Check if student already has an application
            if HostelApplication.objects.filter(student=student, semester=current_semester).exists():
                continue
                
            application = HostelApplication.objects.create(
                student=student,
                room_type=room_type,
                semester=current_semester,
                status=status,
                start_date=current_semester.start_date,
                end_date=current_semester.end_date
            )
            
            # If approved, create room assignment
            if status == 'approved':
                # Find an available room
                available_rooms = Room.objects.filter(
                    room_type=room_type,
                    status='available'
                )
                
                if available_rooms.exists():
                    room = available_rooms.first()
                    
                    # Create room assignment
                    RoomAssignment.objects.create(
                        student=student,
                        room=room,
                        hostel_application=application,
                        start_date=current_semester.start_date,
                        end_date=current_semester.end_date,
                        status='active'
                    )
                    
                    # Update room status
                    room.update_status()
        
        print(f"Created applications. Total: {HostelApplication.objects.count()}")
    else:
        print(f"Using existing {HostelApplication.objects.count()} applications")

if __name__ == "__main__":
    print("Creating sample data for room statistics...")
    create_rooms()
    create_semesters()
    create_applications()
    print("Done!") 