FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Install system dependencies (required for compiling cryptography if needed and general stability)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for caching optimization
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create media and static directories
RUN mkdir -p media static staticfiles shared

# Expose standard port 8000
EXPOSE 8000

# Run migrations, compile static files, and launch high-performance Gunicorn production server
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn securats.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
