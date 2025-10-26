#!/bin/bash

# Smart CCTV System - Quick Setup Script
# This script sets up the environment and installs dependencies

set -e

echo "🔧 Smart CCTV System - Quick Setup"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Check Python version
if [[ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]]; then
    echo "❌ Python 3.8 or later is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "🔨 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔨 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔨 Upgrading pip..."
python -m pip install --upgrade pip

# Install basic dependencies first
echo "🔨 Installing core dependencies..."
pip install wheel setuptools

# Install requirements in stages to handle potential conflicts
echo "🔨 Installing core ML dependencies..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo "🔨 Installing computer vision dependencies..."
pip install opencv-python numpy ultralytics

echo "🔨 Installing audio dependencies..."
pip install pyttsx3 pygame pydub

# Try to install PyAudio (can be problematic on some systems)
echo "🔨 Installing audio I/O dependencies..."
if pip install PyAudio; then
    echo "✅ PyAudio installed successfully"
else
    echo "⚠️  PyAudio installation failed. Audio input may not work."
    echo "   On macOS: brew install portaudio && pip install PyAudio"
    echo "   On Ubuntu: sudo apt install portaudio19-dev && pip install PyAudio"
    echo "   On Windows: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/"
fi

echo "🔨 Installing remaining dependencies..."
pip install -r requirements.txt || echo "⚠️  Some optional dependencies may have failed to install"

# Create necessary directories
echo "🔨 Creating data directories..."
mkdir -p data/logs data/snapshots data/tts_cache models

# Copy example config if config doesn't exist
echo "🔨 Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    if [ -f "config/config.example.yaml" ]; then
        cp config/config.example.yaml config/config.yaml
        echo "✅ Configuration file created from example"
    else
        echo "⚠️  No example configuration found"
    fi
else
    echo "✅ Configuration file already exists"
fi

# Download YOLO model
echo "🔨 Downloading YOLO model..."
python -c "
import os
os.makedirs('models', exist_ok=True)
try:
    from ultralytics import YOLO
    model = YOLO('yolov8n.pt')
    print('✅ YOLO model downloaded successfully')
except Exception as e:
    print(f'⚠️  YOLO model download failed: {e}')
    print('The model will be downloaded automatically on first run')
"

# Test the installation
echo "🔨 Testing installation..."
python test_features.py

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your Smart CCTV System is ready! 🔍📹"
echo ""
echo "📋 Next Steps:"
echo "1. Edit config/config.yaml to configure your cameras"
echo "2. Update camera URLs with your actual RTSP streams"
echo "3. Configure alert rules and speaker settings"
echo "4. Run the system: python src/main.py"
echo ""
echo "📖 For more information, see:"
echo "- README.md for detailed setup instructions"
echo "- docs/ folder for comprehensive documentation"
echo ""
echo "🔧 To activate the environment later:"
echo "   source venv/bin/activate"
echo ""
echo "🚀 To start the system:"
echo "   python src/main.py"
echo ""