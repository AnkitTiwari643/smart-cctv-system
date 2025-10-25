# Quick Start Guide - Handling Installation Issues

## 🚀 **Fastest Solutions (TL;DR)**

### **Option 1: One-Click Setup**
```bash
# Run the automated setup script
chmod +x quick-start.sh
./quick-start.sh
```

### **Option 2: Docker (Recommended)**
```bash
# Copy configuration
cp config/config.example.yaml config/config.yaml

# Edit with your camera URLs
nano config/config.yaml

# Build and run
docker-compose up --build
```

### **Option 3: Minimal Installation**
```bash
# Install only detection dependencies (no audio)
pip install -r requirements-minimal.txt

# Download models manually
python scripts/download_models.py --model yolov8n.pt

# Copy and edit config
cp config/config.example.yaml config/config.yaml

# Run system
python src/main.py
```

## 🔧 **Issue-Specific Solutions**

### **PyAudio Build Errors**

**Quick Fix:**
```bash
# Use minimal requirements (no audio alerts)
pip install -r requirements-minimal.txt
```

**Full Fix (Linux):**
```bash
sudo apt-get install build-essential portaudio19-dev python3-dev
pip install PyAudio
```

**Full Fix (macOS):**
```bash
brew install portaudio
export CPPFLAGS=-I/opt/homebrew/include
export LDFLAGS=-L/opt/homebrew/lib
pip install PyAudio
```

### **YOLO Model Download Errors**

**Manual Download:**
```bash
# Create models directory
mkdir -p models

# Download directly
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt -O models/yolov8n.pt

# Or use the download script
python scripts/download_models.py --model yolov8n.pt
```

**SSL Certificate Issues:**
```bash
# Download with insecure flag
python scripts/download_models.py --model yolov8n.pt --insecure
```

## Detailed Installation Process

### Step 1: Choose Your Installation Method

**Method A: Minimal (Detection Only)**
- ✅ Fastest setup
- ✅ Object detection works perfectly
- ❌ No audio alerts
- ❌ No speaker integration

**Method B: Full Installation**
- ✅ Complete feature set
- ✅ Audio alerts work
- ❌ Requires system dependencies
- ❌ More complex setup

**Method C: Docker**
- ✅ Everything works out of the box
- ✅ No dependency issues
- ✅ Easy deployment
- ❌ Requires Docker knowledge

### Step 2: System Dependencies (If not using Docker)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    portaudio19-dev \
    python3-dev \
    libasound2-dev \
    libportaudio2 \
    ffmpeg
```

**macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install portaudio ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S base-devel portaudio python
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install portaudio-devel python3-devel
```

### Step 3: Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### Step 4: Install Dependencies

**Option A: Minimal**
```bash
pip install -r requirements-minimal.txt
```

**Option B: Try full, fallback to minimal**
```bash
# Try full installation
pip install -r requirements.txt || {
    echo "Full installation failed, installing minimal..."
    pip install -r requirements-minimal.txt
}
```

**Option C: Install audio separately**
```bash
# Install core first
pip install -r requirements-minimal.txt

# Try audio dependencies
pip install -r requirements-audio.txt || echo "Audio disabled"
```

### Step 5: Test Installation

```bash
# Test core functionality
python -c "import cv2, torch, ultralytics; print('✓ Core OK')"

# Test audio (optional)
python -c "import pyttsx3, pyaudio; print('✓ Audio OK')" || echo "⚠ Audio disabled"

# Test object detection
python scripts/detector_example.py
```

### Step 6: Configuration

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit with your settings
nano config/config.yaml
```

## Alternative Audio Solutions

If PyAudio continues to fail, you can use alternatives:

### Option 1: Use system TTS
```python
# In alerts/alert_manager.py, replace pyttsx3 with:
import subprocess

def speak(text):
    # Linux
    subprocess.run(['espeak', text])
    
    # macOS  
    subprocess.run(['say', text])
    
    # Windows
    subprocess.run(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthizer).Speak("{text}")'])
```

### Option 2: Use pygame for audio
```bash
pip install pygame
```

```python
# Simple audio playback without PyAudio
import pygame
pygame.mixer.init()
pygame.mixer.music.load("alert.wav")
pygame.mixer.music.play()
```

### Option 3: Disable audio features
```yaml
# In config.yaml
speakers:
  - name: "disabled"
    type: "none"
    enabled: false

# The system will log alerts instead of playing them
```

## Docker Alternative (Recommended)

If you're still having issues, use Docker:

### 1. Build Container
```bash
docker build -t smart-cctv .
```

### 2. Run with Audio Support
```bash
# Linux (with audio device access)
docker run -it --device=/dev/snd:/dev/snd \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/data:/app/data \
    smart-cctv

# macOS (audio may not work in Docker)
docker run -it \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/data:/app/data \
    smart-cctv

# Windows (with WSL2)
docker run -it \
    -v ${PWD}/config:/app/config \
    -v ${PWD}/data:/app/data \
    smart-cctv
```

### 3. Or use Docker Compose
```bash
docker-compose up --build
```

## Troubleshooting Common Issues

### Issue: "gcc failed: No such file or directory"
**Solution:** Install build tools
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# CentOS/RHEL  
sudo yum groupinstall "Development Tools"

# Alpine
apk add build-base
```

### Issue: "portaudio.h: No such file or directory"
**Solution:** Install PortAudio development headers
```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev

# macOS
brew install portaudio

# CentOS/RHEL
sudo yum install portaudio-devel
```

### Issue: "Microsoft Visual C++ 14.0 is required" (Windows)
**Solution:** Install Visual Studio Build Tools
1. Download from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
2. Install "C++ build tools" workload

### Issue: Performance problems
**Solution:** Use minimal requirements
```bash
pip uninstall PyAudio pyttsx3 pydub
pip install -r requirements-minimal.txt

# Disable audio in config
# Set speakers.enabled: false
```

## Verification Steps

After installation, verify everything works:

```bash
# 1. Test imports
python -c "
try:
    import cv2, torch, ultralytics, numpy as np
    print('✓ Core dependencies working')
    
    from ultralytics import YOLO
    model = YOLO('yolov8n.pt')
    print('✓ YOLO model working')
    
    import pyttsx3, pyaudio
    print('✓ Audio dependencies working')
except ImportError as e:
    print(f'⚠️ Import error: {e}')
"

# 2. Test object detection
python scripts/test_detection.py --webcam --duration 10

# 3. Test full system (dry run)
python src/main.py --config config/config.yaml
```

## Getting Help

If you're still having issues:

1. **Check logs**: Look at error messages carefully
2. **Try Docker**: Easiest way to avoid dependency issues  
3. **Use minimal install**: Skip audio features if needed
4. **Check platform**: Some features work better on certain OS
5. **Update system**: Ensure you have latest packages

The system is designed to work even without audio features - you'll still get visual detection, logging, and web alerts.