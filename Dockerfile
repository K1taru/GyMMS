# syntax=docker/dockerfile:1
FROM python:3.14.8-slim-trixie

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Fixed application identity
RUN groupadd --gid 10001 gymms && useradd --uid 10001 --gid gymms --no-create-home gymms

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# Copy Django project
COPY . .
RUN mkdir -p /app/staticfiles /app/media && chown gymms:gymms /app/staticfiles /app/media
USER 10001:10001

# Expose Gunicorn port
EXPOSE 8000
