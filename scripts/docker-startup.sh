#!/bin/bash
# Docker startup script for Smart CCTV System

set -e

echo "🚀 Smart CCTV System - Docker Startup"
echo "====================================="

# Create required directories
mkdir -p /app/models /app/data/logs /app/data/snapshots /app/data/tts_cache

# Set proper permissions
# chown -R cctv:cctv /app/models /app/data || true

echo "📁 Directory structure created"

# Download YOLO models
echo "🤖 Downloading YOLO models..."
python -c "
import os
import sys
try:
    from ultralytics import YOLO
    print('Attempting to download yolov8n.pt...')
    model = YOLO('yolov8n.pt')
    print('✅ YOLO model downloaded successfully')
except Exception as e:
    print(f'⚠️ Model download failed: {e}')
    print('The system will attempt to download at runtime')
    # Don't exit - continue with startup
" || echo "⚠️ Model download failed, continuing..."

echo "🔧 Testing core dependencies..."
python -c "
import cv2, torch, numpy as np
print('✅ Core dependencies working')
try:
    import ultralytics
    print('✅ Ultralytics available')
except ImportError:
    print('⚠️ Ultralytics not available')

try:
    import pyaudio, pyttsx3
    print('✅ Audio dependencies available')
except ImportError:
    print('⚠️ Audio dependencies not available (detection-only mode)')
"

# Check if config exists
if [ ! -f "/app/config/config.yaml" ]; then
    echo "⚠️ No config.yaml found in mounted volume"
    if [ -f "/app/config/config.example.yaml" ]; then
        echo "📝 Found config.example.yaml, but cannot copy to read-only volume"
        echo ""
        echo "🔧 To fix this issue:"
        echo "1. Stop the container (Ctrl+C)"
        echo "2. Run on your host machine:"
        echo "   cp config/config.example.yaml config/config.yaml"
        echo "3. Edit the config file:"
        echo "   nano config/config.yaml"
        echo "4. Restart with: docker-compose up"
        echo ""
        echo "Or use the setup script: ./docker-setup.sh"
        
        # Give user time to see the message
        echo "Waiting 10 seconds before exit..."
        sleep 10
        exit 1
    else
        echo "❌ No config.example.yaml found in mounted config directory"
        echo "Please ensure the config directory is properly mounted"
        exit 1
    fi
else
    echo "✅ Configuration file found"
fi

echo "🎥 Starting Smart CCTV System..."
echo "Press Ctrl+C to stop"
echo ""

# Start the main application
exec python src/main.py --config config/config.yaml