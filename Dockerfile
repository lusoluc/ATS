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

# Versions-Metadaten (P0.1) – wird im Release-Workflow per --build-arg gesetzt
ARG SECURATS_VERSION=dev
LABEL org.opencontainers.image.title="SecurATS" \
      org.opencontainers.image.source="https://github.com/lusoluc/ATS" \
      org.opencontainers.image.version="${SECURATS_VERSION}"

# Expose standard port 8000
EXPOSE 8000

# Healthcheck gegen /healthz/ (ohne curl-Abhängigkeit)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=4); sys.exit(0 if r.status==200 else 1)" || exit 1

# Entrypoint übernimmt Warten-auf-DB, Migrationen, collectstatic, Bootstrap;
# CMD ist der eigentliche Serverprozess (im Worker-Service überschreibbar).
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "securats.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
