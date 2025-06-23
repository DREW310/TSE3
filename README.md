# MMU Hostel Management System

Hey there! This is our TSE6223 Software Engineering Fundamentals project for the MMU Hostel Management System. We've been working super hard on this throughout the semester. It's a web application built with Django that helps manage student hostel applications and room assignments.

## Group Information
**Group Name:** Byte Me  
**Lecture Section:** SE1  
**Lab Section:** 1D  

### Team Members
| Student ID | Student Name          |
|------------|-----------------------|
| 1211109457 | DO WAI LUNG           |
| 1221305730 | DORIS HENG            | 
| 1211111904 | ELDEENA LIM HUEY YINN |
| 1211108301 | KONG YI XUAN          |

## Project Overview

We created this system to solve the problems we noticed with the current hostel application process. It was frustrating how manual everything was, so we wanted to make something that would make life easier for both students and staff.

Our system has these main features:
- Student hostel application portal
- Admin dashboard for hostel management
- First-come-first-serve quota system for room assignments
- Room occupancy tracking and statistics
- Maintenance request system

## What We Learned

This project taught us so much! We struggled with Django at first (those models were confusing!), but eventually got the hang of it. We learned about:
- Building web applications with Django
- Creating user authentication systems
- Database design and management
- Working with Bootstrap for responsive design
- Implementing business logic for hostel management

The hardest part was probably setting up the quota system for room assignments. We had to make sure applications were processed in order and that the system would automatically reject applications when quotas were reached.

## How to Run Our Project

1. Clone the repository:
```bash
git clone [repository-url]
cd TSE Project
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser (for admin access):
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Open your browser and go to:
```
http://127.0.0.1:8000/
```

## Project Structure

Our project is organized like this:
- `hostel_management/` - Main project settings
- `apps/` - Django applications
  - `accounts/` - User authentication and profiles
  - `hostel/` - Hostel management features

## User Types and Features

### Student Features
- Apply for hostel accommodation
- View application status
- Submit maintenance requests
- View room details and payment information

### Staff/Admin Features
- Process student applications
- Manage room assignments
- View room statistics and reports
- Handle maintenance requests

## Challenges We Faced

We ran into a bunch of issues during development:
1. Getting the quota system to work correctly was tricky
2. Figuring out how to handle room assignments efficiently
3. Making sure the application process was fair and transparent
4. Dealing with edge cases like what happens when a student cancels their application

It was a great learning experience figuring out solutions to these problems. We had to rewrite some parts of the code multiple times until we got it right.

## Future Improvements

If we had more time, we'd love to add:
- Online payment integration
- Mobile app version
- Room selection map interface
- Roommate matching system
- Notification system for application status updates

## Conclusion

This project was a great opportunity to apply what we've learned in class to a real-world problem. We're proud of what we've built and hope it can actually be implemented to help MMU students and staff with the hostel application process!

Thanks for checking out our project! :) 