import os
import subprocess
import sys

def run_command(command):
    """Helper function to run shell commands"""
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Successfully executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")
        sys.exit(1)

def create_directory(path):
    """Helper function to create directories"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def main():
    # Create virtual environment
    print("Creating virtual environment...")
    run_command("python -m venv venv")
    
    # Activate virtual environment and install requirements
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate && "
    else:
        activate_cmd = "source venv/bin/activate && "
    
    print("Installing requirements...")
    run_command(f"{activate_cmd}pip install -r requirements.txt")
    
    # Create Django project
    print("Creating Django project...")
    run_command(f"{activate_cmd}django-admin startproject hostel_management .")
    
    # Create apps directory
    create_directory("apps")
    
    # Create Django apps
    apps = ["accounts", "hostel", "payments", "maintenance", "announcements"]
    for app in apps:
        print(f"Creating {app} app...")
        run_command(f"{activate_cmd}python manage.py startapp {app} apps/{app}")
    
    print("\nProject setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment")
    print("2. Create a .env file with your configuration")
    print("3. Run migrations: python manage.py migrate")
    print("4. Create a superuser: python manage.py createsuperuser")
    print("5. Run the development server: python manage.py runserver")

if __name__ == "__main__":
    main() 