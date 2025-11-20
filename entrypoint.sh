#!/bin/bash

# Exit on error
set -e

echo "Starting entrypoint script..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create default superuser if no users exist
echo "Creating default superuser if needed..."
python manage.py create_default_superuser

echo "Starting Gunicorn server..."
# Start Gunicorn
exec gunicorn gbnqr.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
