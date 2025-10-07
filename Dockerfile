# Django + PostgreSQL (Docker)

# Use an official Python image
FROM python:3.11-slim

# Disable .pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose Django port
EXPOSE 8000

# Run Django server (for development)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
