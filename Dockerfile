FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for PyAudio and web interface
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    portaudio19-dev \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    espeak \
    libespeak-dev \
    python3-dev \
    wget \
    curl \
    sqlite3 \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements in order of dependency complexity
COPY requirements.txt .
COPY requirements-minimal.txt .
COPY requirements-audio.txt .

# Install all dependencies including Flask web interface
RUN pip install --no-cache-dir -r requirements.txt

# Install minimal dependencies (fallback)
RUN pip install --no-cache-dir -r requirements-minimal.txt || echo "Minimal requirements already satisfied"

# Try to install audio dependencies, continue if they fail
RUN pip install --no-cache-dir -r requirements-audio.txt || \
    echo "Audio dependencies failed, continuing without audio support"

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY run_web.py .
COPY start_system.py .
COPY demo_web.py .

# Make startup scripts executable
RUN chmod +x scripts/docker-startup.sh
RUN chmod +x run_web.py start_system.py demo_web.py

# Create data directories
RUN mkdir -p data/logs data/snapshots data/tts_cache models data/alerts

# Create web interface data directory and database
RUN mkdir -p data/web && touch data/alerts.db

# COPY YOLO model during build to avoid SSL issues at runtime
COPY resources/yolov8n.pt  ./models/yolov8n.pt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV YOLO_CONFIG_DIR=/app/models

# Create non-root user for security
# RUN useradd -m -u 1000 cctv && chown -R cctv:cctv /app
# USER cctv

# Expose ports for web interface and main service
EXPOSE 5000
EXPOSE 8080

# Health check for both services
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || python -c "import sys; sys.path.append('src'); from utils.config_loader import ConfigLoader; print('OK')" || exit 1

# Run complete system (CCTV + Web Interface)
CMD ["python", "start_system.py"]
