# Installation Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- 4 IP cameras with RTSP/HTTP streaming
- Laptop/computer meeting minimum hardware requirements (see `02-hardware-setup.md`)
- Speaker (wired or Bluetooth)

## Installation Steps

### 1. System Preparation

#### Ubuntu/Debian Linux
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
    python3.9 python3-pip python3-dev \
    git ffmpeg libsm6 libxext6 \
    portaudio19-dev python3-pyaudio \
    espeak libespeak-dev \
    bluetooth libbluetooth-dev

# Optional: Install CUDA (if NVIDIA GPU)
# Follow NVIDIA CUDA installation guide
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.9 git ffmpeg portaudio espeak

# Install PyAudio
pip3 install pyaudio
```

#### Windows
```powershell
# Install Python 3.9+ from python.org
# Install Git from git-scm.com

# Install FFmpeg
# Download from ffmpeg.org and add to PATH

# PyAudio installation (Windows)
pip install pipwin
pipwin install pyaudio
```

### 2. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-cctv-system.git
cd smart-cctv-system

# Or if you received as ZIP
unzip smart-cctv-system.zip
cd smart-cctv-system
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 4. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# This will install:
# - OpenCV for video processing
# - PyTorch for deep learning
# - YOLO v8 for object detection
# - Audio libraries for alerts
# - And all other dependencies
```

### 5. Download Pre-trained Models

```bash
# Create models directory
mkdir -p models

# Download YOLO v8 nano model (automatic on first run, or manual)
python3 -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt')"

# Model will be downloaded to ~/.cache/ultralytics/
# Or copy to models/ directory
```

### 6. Configure System

```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit configuration with your settings
nano config/config.yaml
# OR
vim config/config.yaml
# OR use any text editor
```

**Important configuration items**:
- Camera URLs (RTSP addresses)
- Camera credentials
- Reference points and distances
- Alert rules
- Speaker settings

### 7. Camera Calibration (Optional but Recommended)

For accurate distance measurement:

```bash
# Run calibration script for each camera
python3 scripts/calibrate_camera.py --camera camera_1

# Follow on-screen instructions
# Hold chessboard pattern in view
# Capture 20-30 images at different angles
# Calibration data saved to config/calibration/camera_1.json

# Repeat for all cameras
python3 scripts/calibrate_camera.py --camera camera_2
python3 scripts/calibrate_camera.py --camera camera_3
python3 scripts/calibrate_camera.py --camera camera_4
```

### 8. Test Camera Connections

```bash
# Test all cameras
python3 scripts/test_cameras.py

# Should output:
# ✓ camera_1 (Front Door): Connected, 1920x1080 @ 25fps
# ✓ camera_2 (Backyard): Connected, 1920x1080 @ 25fps
# ✓ camera_3 (Side Entrance): Connected, 1920x1080 @ 25fps
# ✓ camera_4 (Garage): Connected, 1920x1080 @ 25fps
```

### 9. Test Speaker/Audio Output

```bash
# Test wired speaker
python3 scripts/test_audio.py --speaker living_room

# Test Bluetooth speaker (if configured)
python3 scripts/test_audio.py --speaker bedroom

# Should play test message
```

### 10. Run System Test

```bash
# Run in test mode (processes for 60 seconds then exits)
python3 src/main.py --config config/config.yaml

# Check output for:
# - All cameras connected
# - Detection working
# - No errors
```

## Troubleshooting Installation Issues

### Issue: PyAudio installation fails

**Linux**:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**macOS**:
```bash
brew install portaudio
pip install pyaudio
```

**Windows**:
```bash
pip install pipwin
pipwin install pyaudio
```

### Issue: OpenCV can't read camera streams

Check FFmpeg installation:
```bash
ffmpeg -version

# If not installed:
# Ubuntu: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from ffmpeg.org
```

### Issue: CUDA not found (if using GPU)

```bash
# Check CUDA installation
nvidia-smi

# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Bluetooth speaker not connecting

**Linux**:
```bash
# Install bluetooth packages
sudo apt-get install bluez python3-bluez

# Pair speaker manually first
bluetoothctl
> scan on
> pair AA:BB:CC:DD:EE:FF
> trust AA:BB:CC:DD:EE:FF
> connect AA:BB:CC:DD:EE:FF
```

### Issue: Permission denied errors

```bash
# Give execute permissions
chmod +x scripts/*.py

# Run with sudo if needed (not recommended)
sudo python3 src/main.py
```

## Post-Installation Setup

### 1. Create Directories

```bash
# These are created automatically, but you can pre-create:
mkdir -p data/logs
mkdir -p data/snapshots
mkdir -p data/tts_cache
mkdir -p config/calibration
```

### 2. Set Up Automatic Startup (Optional)

#### Linux (systemd)
```bash
# Copy service file
sudo cp scripts/smart-cctv.service /etc/systemd/system/

# Edit paths in service file
sudo nano /etc/systemd/system/smart-cctv.service

# Enable and start service
sudo systemctl enable smart-cctv
sudo systemctl start smart-cctv

# Check status
sudo systemctl status smart-cctv
```

#### macOS (launchd)
```bash
# Copy plist file
cp scripts/com.smartcctv.plist ~/Library/LaunchAgents/

# Load service
launchctl load ~/Library/LaunchAgents/com.smartcctv.plist
```

#### Windows (Task Scheduler)
Use Windows Task Scheduler to create a startup task running:
```
python C:\path\to\smart-cctv-system\src\main.py
```

### 3. Configure Firewall (if using web UI)

```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp

# macOS
# System Preferences > Security & Privacy > Firewall > Firewall Options
# Add Python

# Windows
# Windows Defender Firewall > Allow an app
# Add Python
```

## Verification Checklist

After installation, verify:

- [ ] All cameras accessible and streaming
- [ ] Object detection working (test with yourself on camera)
- [ ] Distance calculation producing reasonable values
- [ ] Alerts triggering based on rules
- [ ] Audio playing through speaker
- [ ] Logs being written to `data/logs/`
- [ ] Events being saved to database
- [ ] Snapshots being saved
- [ ] System running without crashes for 10+ minutes

## Quick Start Command

Once installed and configured:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Run the system
python src/main.py --config config/config.yaml
```

## Updating the System

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart system
sudo systemctl restart smart-cctv  # Linux with systemd
# or manually stop and start
```

## Uninstallation

```bash
# Stop service (if installed)
sudo systemctl stop smart-cctv
sudo systemctl disable smart-cctv
sudo rm /etc/systemd/system/smart-cctv.service

# Deactivate virtual environment
deactivate

# Remove directory
cd ..
rm -rf smart-cctv-system
```

## Getting Help

- Check logs: `tail -f data/logs/app.log`
- Check errors: `tail -f data/logs/errors.log`
- Test components individually using scripts in `scripts/`
- See documentation in `docs/` folder

## Next Steps

- Read `docs/05-alert-system.md` for alert configuration
- Read `docs/06-security-privacy.md` for security best practices
- Read `docs/07-testing-verification.md` for testing strategies
