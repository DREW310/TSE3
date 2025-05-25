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

1. Clone the repository:
```bash
git clone [repository-url]
cd hostel-management
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

5. Set up environment variables:
Create a `.env` file in the project root with:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://username:password@localhost:5432/hostel_db
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Run the development server:
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

## Development Guidelines

### Version Control
- Use meaningful commit messages
- Create feature branches for new development
- Follow the branching strategy:
  - `main` - Production-ready code
  - `develop` - Development branch
  - `feature/*` - New features
  - `bugfix/*` - Bug fixes
  - `hotfix/*` - Urgent production fixes

### Code Style
- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions small and focused

### Testing
- Write tests for new features
- Run tests before committing:
```bash
python manage.py test
```
- Maintain test coverage above 80%

### Ignored Files
The following files and directories are ignored by git:
- Python bytecode and cache files (`__pycache__/`, `*.pyc`, etc.)
- Virtual environment (`venv/`)
- Environment files (`.env`)
- IDE-specific files (`.vscode/`, `.idea/`)
- Database files (`*.sqlite3`, `*.db`)
- Coverage reports (`htmlcov/`, `.coverage`)
- Build and distribution files (`dist/`, `build/`)
- Node modules (`node_modules/`)

## Development Team

- [Your Name] - Project Lead
- [Team Member 1] - Backend Developer
- [Team Member 2] - Frontend Developer
- [Team Member 3] - Database Designer

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 