# MMU Hostel Management System

A web-based system for managing hostel accommodations at MMU, built with Django and Bootstrap 5.

## Features

- Student hostel application and management
- Admin dashboard for hostel management
- Room allocation system
- Payment tracking with QR code support
- Maintenance request system
- Announcement system

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://username:password@localhost:5432/hostel_db
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

- `hostel_management/` - Main project directory
- `apps/` - Django applications
  - `accounts/` - User authentication and profiles
  - `hostel/` - Hostel management features
  - `payments/` - Payment processing
  - `maintenance/` - Maintenance request system
  - `announcements/` - Announcement system

## Development Team

- [Your Name] - Project Lead
- [Team Member 1] - Backend Developer
- [Team Member 2] - Frontend Developer
- [Team Member 3] - Database Designer 