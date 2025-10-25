#!/bin/bash
# Quick Start Script for Smart CCTV System
# Handles PyAudio and YOLO model download issues

set -e

echo "🚀 Smart CCTV System - Quick Start"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions for colored output
error() { echo -e "${RED}❌ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    error "Please run this script from the smart-cctv-system directory"
    exit 1
fi

# Function to test Python environment
test_python() {
    info "Testing Python environment..."
    
    # Test core dependencies
    python3 -c "
import sys
missing = []
try:
    import cv2
    print('✓ OpenCV')
except ImportError:
    missing.append('opencv-python')

try:
    import numpy
    print('✓ NumPy')
except ImportError:
    missing.append('numpy')

try:
    import torch
    print('✓ PyTorch')
except ImportError:
    missing.append('torch')

try:
    import ultralytics
    print('✓ Ultralytics')
except ImportError:
    missing.append('ultralytics')

try:
    import loguru
    print('✓ Loguru')
except ImportError:
    missing.append('loguru')

if missing:
    print(f'Missing: {missing}')
    sys.exit(1)
else:
    print('✅ All core dependencies available')
" 2>/dev/null
    
    return $?
}

# Function to install minimal dependencies
install_minimal() {
    info "Installing minimal dependencies (detection only)..."
    
    if [ ! -f "requirements-minimal.txt" ]; then
        error "requirements-minimal.txt not found"
        return 1
    fi
    
    pip3 install -r requirements-minimal.txt
    return $?
}

# Function to download YOLO models
download_models() {
    info "Downloading YOLO models..."
    
    mkdir -p models
    
    # Try using the download script
    if [ -f "scripts/download_models.py" ]; then
        python3 scripts/download_models.py --model yolov8n.pt 2>/dev/null && return 0
    fi
    
    # Fallback: manual download using wget/curl
    MODEL_URL="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    MODEL_FILE="models/yolov8n.pt"
    
    if [ ! -f "$MODEL_FILE" ]; then
        info "Attempting manual download..."
        
        if command -v wget >/dev/null 2>&1; then
            wget -q --show-progress "$MODEL_URL" -O "$MODEL_FILE" 2>/dev/null && return 0
        elif command -v curl >/dev/null 2>&1; then
            curl -L -o "$MODEL_FILE" "$MODEL_URL" 2>/dev/null && return 0
        fi
    else
        success "Model already exists: $MODEL_FILE"
        return 0
    fi
    
    warning "Model download failed - will attempt at runtime"
    return 1
}

# Function to create config if needed
setup_config() {
    info "Setting up configuration..."
    
    if [ ! -f "config/config.yaml" ]; then
        if [ -f "config/config.example.yaml" ]; then
            cp config/config.example.yaml config/config.yaml
            success "Created config/config.yaml from example"
            warning "Please edit config/config.yaml with your camera URLs"
        else
            error "config.example.yaml not found"
            return 1
        fi
    else
        success "Configuration file already exists"
    fi
}

# Function to test installation
test_installation() {
    info "Testing installation..."
    
    # Test Python dependencies
    if ! test_python; then
        error "Python dependencies test failed"
        return 1
    fi
    
    # Test object detector
    python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    from detection.object_detector import ObjectDetector
    from utils.config_loader import ConfigLoader
    
    config = ConfigLoader('config/config.yaml')
    detector = ObjectDetector(config)
    print('✅ Object detector initialized successfully')
except Exception as e:
    print(f'❌ Object detector test failed: {e}')
    sys.exit(1)
" 2>/dev/null
    
    return $?
}

# Main installation flow
main() {
    echo
    info "Choose installation method:"
    echo "1) Docker (recommended - handles all dependencies)"
    echo "2) Local installation (minimal - detection only)"
    echo "3) Local installation (full - with audio support)"
    echo "4) Test existing installation"
    echo
    
    read -p "Enter choice (1-4): " choice
    echo
    
    case $choice in
        1)
            info "Using Docker installation..."
            if ! command -v docker >/dev/null 2>&1; then
                error "Docker not found. Please install Docker first."
                exit 1
            fi
            
            if ! command -v docker-compose >/dev/null 2>&1; then
                error "Docker Compose not found. Please install Docker Compose first."
                exit 1
            fi
            
            setup_config
            
            info "Building Docker image..."
            docker-compose build
            
            info "Starting Smart CCTV system in Docker..."
            docker-compose up
            ;;
            
        2)
            info "Local minimal installation..."
            
            # Install minimal dependencies
            if ! install_minimal; then
                error "Failed to install minimal dependencies"
                exit 1
            fi
            
            # Download models
            download_models || warning "Model download failed - will retry at runtime"
            
            # Setup config
            setup_config
            
            # Test installation
            if test_installation; then
                success "Installation completed successfully!"
                echo
                info "Next steps:"
                echo "1. Edit config/config.yaml with your camera URLs"
                echo "2. Run: python3 src/main.py"
            else
                error "Installation test failed"
                exit 1
            fi
            ;;
            
        3)
            info "Local full installation..."
            warning "This may fail due to PyAudio dependencies"
            
            # Try full installation
            pip3 install -r requirements.txt || {
                warning "Full installation failed, falling back to minimal..."
                install_minimal || {
                    error "Even minimal installation failed"
                    exit 1
                }
            }
            
            # Download models
            download_models || warning "Model download failed - will retry at runtime"
            
            # Setup config
            setup_config
            
            # Test installation
            if test_installation; then
                success "Installation completed successfully!"
                echo
                info "Next steps:"
                echo "1. Edit config/config.yaml with your camera URLs"
                echo "2. Run: python3 src/main.py"
            else
                error "Installation test failed"
                exit 1
            fi
            ;;
            
        4)
            info "Testing existing installation..."
            
            if test_installation; then
                success "Installation test passed!"
                echo
                info "You can run: python3 src/main.py"
            else
                error "Installation test failed"
                echo
                info "Try running option 2 (minimal installation)"
                exit 1
            fi
            ;;
            
        *)
            error "Invalid choice"
            exit 1
            ;;
    esac
}

# Check if running in Docker
if [ -f /.dockerenv ]; then
    error "This script should not be run inside Docker"
    error "Use: docker-compose up --build"
    exit 1
fi

# Run main function
main "$@"