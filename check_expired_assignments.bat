@echo off
REM Navigate to the project directory
cd /d C:\path\to\project

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the Django management command
python manage.py check_expired_assignments

REM Log the execution
echo %date% %time%: Executed check_expired_assignments >> cron.log 