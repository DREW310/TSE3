#!/bin/bash

# Navigate to the project directory
cd /path/to/project

# Activate the virtual environment
source venv/bin/activate

# Run the Django management command
python manage.py check_expired_assignments

# Log the execution
echo "$(date): Executed check_expired_assignments" >> /path/to/project/cron.log 