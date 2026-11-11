#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Apply database migrations (if any).
python manage.py migrate --noinput

# Collect static files for production.
python manage.py collectstatic --noinput

# Start the Gunicorn server. Adjust workers as needed.
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

