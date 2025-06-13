# Automatic Removal of Expired Room Assignments

This system automatically marks room assignments as "completed" when their end date has passed, which effectively removes the student from the room and updates the room's availability status.

## How It Works

1. The system includes a Django management command (`check_expired_assignments`) that:
   - Checks for room assignments that have end dates in the past
   - Marks these assignments as "completed"
   - Updates the room status accordingly

2. When a room assignment is marked as completed:
   - The student is no longer listed as an occupant of the room
   - The room's remaining capacity is updated
   - If no other students are assigned to the room, its status changes to "available"

## Setting Up Automatic Daily Checks

### On Linux/Unix Systems (using cron)

1. Make the shell script executable:
   ```
   chmod +x check_expired_assignments.sh
   ```

2. Edit the script to use the correct paths for your environment:
   ```
   nano check_expired_assignments.sh
   ```

3. Add a cron job to run the script daily (e.g., at 1:00 AM):
   ```
   crontab -e
   ```

4. Add this line to the crontab:
   ```
   0 1 * * * /path/to/check_expired_assignments.sh
   ```

### On Windows Systems (using Task Scheduler)

1. Edit the batch file to use the correct paths for your environment:
   ```
   check_expired_assignments.bat
   ```

2. Open Task Scheduler:
   - Create a new task
   - Set it to run daily at your preferred time (e.g., 1:00 AM)
   - Action: Start a program
   - Program/script: Path to the batch file

## Manual Execution

You can also run the command manually to check and update expired assignments:

```
python manage.py check_expired_assignments
```

This will print a message indicating how many assignments were marked as completed. 