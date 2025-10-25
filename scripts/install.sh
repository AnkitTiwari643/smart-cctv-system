#!/bin/bash
# Smart CCTV System Installation Script
# Handles platform-specific dependencies and PyAudio issues

set -e  # Exit on any error

echo "🔧 Smart CCTV System Installation"
echo "=================================="

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
else
    PLATFORM="unknown"
fi

echo "Detected platform: $PLATFORM"

# Function to install system dependencies
install_system_deps() {
    echo "📦 Installing system dependencies..."
    
    case $PLATFORM in
        "linux")
            echo "Installing Linux dependencies..."
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                portaudio19-dev \
                python3-dev \
                libasound2-dev \
                libportaudio2 \
                libportaudiocpp0 \
                ffmpeg \
                libsm6 \
                libxext6 \
                libfontconfig1 \
                libxrender1 \
                libgl1-mesa-glx
            ;;
        "macos")
            echo "Installing macOS dependencies..."
            if ! command -v brew &> /dev/null; then
                echo "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install portaudio ffmpeg
            ;;
        "windows")
            echo "Windows detected - system dependencies not needed for PyAudio"
            ;;
        *)
            echo "⚠️  Unknown platform - you may need to install audio libraries manually"
            ;;
    esac
}

# Function to create virtual environment
create_venv() {
    echo "🐍 Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✓ Virtual environment created"
    else
        echo "✓ Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    echo "✓ Pip upgraded"
}

# Function to install Python dependencies
install_python_deps() {
    echo "📚 Installing Python dependencies..."
    
    # Install minimal requirements first (without audio)
    echo "Installing core dependencies..."
    pip install -r requirements-minimal.txt
    echo "✓ Core dependencies installed"
    
    # Try to install audio dependencies
    echo "Attempting to install audio dependencies..."
    if pip install -r requirements-audio.txt; then
        echo "✓ Audio dependencies installed successfully"
        AUDIO_SUPPORT=true
    else
        echo "⚠️  Audio dependencies failed - continuing without audio support"
        echo "   You can run the system with detection only (no audio alerts)"
        AUDIO_SUPPORT=false
    fi
}

# Function to download YOLO models
download_models() {
    echo "🤖 Downloading YOLO models..."
    
    mkdir -p models
    
    # Create a simple Python script to download YOLO models
    cat > download_models.py << 'EOF'
from ultralytics import YOLO
import os

models_dir = "models"
os.makedirs(models_dir, exist_ok=True)

models = ["yolov8n.pt", "yolov8s.pt"]

for model_name in models:
    print(f"Downloading {model_name}...")
    model = YOLO(model_name)
    print(f"✓ {model_name} downloaded")

print("✓ All models downloaded successfully")
EOF

    python download_models.py
    rm download_models.py
    echo "✓ YOLO models downloaded"
}

# Function to test installation
test_installation() {
    echo "🧪 Testing installation..."
    
    # Test core dependencies
    python -c "
import cv2
import torch
import ultralytics
import numpy as np
from ultralytics import YOLO
print('✓ Core dependencies working')
"
    
    # Test audio dependencies if available
    if [ "$AUDIO_SUPPORT" = true ]; then
        python -c "
try:
    import pyttsx3
    import pyaudio
    print('✓ Audio dependencies working')
except ImportError as e:
    print(f'⚠️  Audio import issue: {e}')
" || echo "⚠️  Audio testing failed but continuing..."
    fi
    
    # Test object detector
    if [ -f "scripts/detector_example.py" ]; then
        echo "Testing object detector..."
        python scripts/detector_example.py || echo "⚠️  Detector test failed"
    fi
}

# Function to create configuration
setup_config() {
    echo "⚙️  Setting up configuration..."
    
    if [ ! -f "config/config.yaml" ]; then
        cp config/config.example.yaml config/config.yaml
        echo "✓ Configuration file created at config/config.yaml"
        echo "  → Edit this file with your camera URLs and settings"
    else
        echo "✓ Configuration file already exists"
    fi
}

# Main installation process
main() {
    echo "Starting installation process..."
    echo
    
    # Check if we're in the right directory
    if [ ! -f "requirements-minimal.txt" ]; then
        echo "❌ Error: Please run this script from the smart-cctv-system directory"
        exit 1
    fi
    
    # Install system dependencies (with user confirmation)
    read -p "Install system dependencies? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_system_deps
    else
        echo "⚠️  Skipping system dependencies - you may need to install audio libraries manually"
    fi
    
    # Create virtual environment
    create_venv
    
    # Install Python dependencies
    install_python_deps
    
    # Download models
    download_models
    
    # Setup configuration
    setup_config
    
    # Test installation
    test_installation
    
    echo
    echo "🎉 Installation completed!"
    echo
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Edit configuration: nano config/config.yaml"
    echo "3. Test cameras: python scripts/test_cameras.py"
    echo "4. Test detection: python scripts/test_detection.py --webcam"
    echo "5. Run system: python src/main.py"
    echo
    
    if [ "$AUDIO_SUPPORT" = false ]; then
        echo "⚠️  Note: Audio alerts are disabled due to installation issues"
        echo "   The system will work for detection and visual alerts only"
        echo "   To enable audio later, install: pip install -r requirements-audio.txt"
    fi
}

# Run main function
main "$@"