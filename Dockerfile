FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for PyAudio
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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements in order of dependency complexity
COPY requirements-minimal.txt .
COPY requirements-audio.txt .

# Install minimal dependencies first
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Try to install audio dependencies, continue if they fail
RUN pip install --no-cache-dir -r requirements-audio.txt || \
    echo "Audio dependencies failed, continuing without audio support"

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Make startup script executable
RUN chmod +x scripts/docker-startup.sh

# Create data directories
RUN mkdir -p data/logs data/snapshots data/tts_cache models

# COPY YOLO model during build to avoid SSL issues at runtime
COPY resources/yolov8n.pt  ./models/yolov8n.pt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV YOLO_CONFIG_DIR=/app/models

# Create non-root user for security
# RUN useradd -m -u 1000 cctv && chown -R cctv:cctv /app
# USER cctv

# Expose port for web interface (optional)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.path.append('src'); from utils.config_loader import ConfigLoader; print('OK')" || exit 1

# Run application
CMD ["./scripts/docker-startup.sh"]
