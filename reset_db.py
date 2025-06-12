import os
import psycopg2
import django
from django.conf import settings

# Get database settings from Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

# Database connection parameters
db_settings = settings.DATABASES['default']
db_name = db_settings['NAME']
db_user = db_settings['USER']
db_password = db_settings['PASSWORD']
db_host = db_settings['HOST']
db_port = db_settings['PORT']

# Connect to PostgreSQL server (default database)
conn = psycopg2.connect(
    dbname='postgres',
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port
)
conn.autocommit = True
cursor = conn.cursor()

# Close all connections to the database
cursor.execute(f"""
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{db_name}'
AND pid <> pg_backend_pid();
""")

# Drop and recreate the database
print(f"Dropping database '{db_name}'...")
cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
print(f"Creating database '{db_name}'...")
cursor.execute(f"CREATE DATABASE {db_name}")

# Close connection
cursor.close()
conn.close()

print("Database reset complete. Now run 'python manage.py migrate' to apply migrations.") 