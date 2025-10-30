#!/bin/bash
# Docker startup script for Smart CCTV System with Web Interface

set -e

echo "🚀 Smart CCTV System - Docker Startup"
echo "====================================="

# Create required directories
mkdir -p /app/models /app/data/logs /app/data/snapshots /app/data/tts_cache /app/data/web

# Set proper permissions
# chown -R cctv:cctv /app/models /app/data || true

echo "📁 Directory structure created"

# Initialize database if it doesn't exist
echo "📊 Initializing database..."
python -c "
import sys
sys.path.append('/app/src')
try:
    from web_interface import init_database
    init_database()
    print('✅ Database initialized')
except Exception as e:
    print(f'⚠️ Database initialization failed: {e}')
    print('Will attempt to initialize at runtime')
"

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
    import flask, flask_socketio
    print('✅ Web interface dependencies available')
except ImportError:
    print('⚠️ Web interface dependencies not available')

try:
    from gtts import gTTS
    print('✅ gTTS (Google Text-to-Speech) available')
except ImportError:
    print('⚠️ gTTS not available - audio alerts disabled')
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

echo "🎥 Starting Smart CCTV System with Web Interface..."
echo "🌐 Web interface will be available at: http://localhost:5000"
echo "🔐 Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the complete system (CCTV + Web Interface)
exec python start_system.py