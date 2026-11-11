# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files for production
RUN python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Entrypoint script (handles migrations, etc.)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default command uses gunicorn (via entrypoint)
CMD ["/entrypoint.sh"]
