# Base image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY . .

# Expose Gunicorn port
EXPOSE 8000
