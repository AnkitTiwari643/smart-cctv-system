# Smart CCTV System with AI Detection and Alerts

## Overview
An advanced home security system that enhances basic 4-camera CCTV with AI-powered object detection, distance calculation, and real-time audio alerts.

## Key Features
- **Real-time Object Detection**: Identifies humans, vehicles, animals, and other objects
- **Movement Tracking**: Tracks detected objects across frames
- **Distance Calculation**: Measures distance between humans and critical areas/vehicles
- **Smart Alerts**: Sends real-time audio messages via wired or Bluetooth speakers
- **Scalable Architecture**: Runs on old laptop, expandable to more powerful systems
- **Privacy-Focused**: Local processing with security best practices

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Configure system
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings

# Run the system
python src/main.py
```

## Documentation Structure
- `docs/01-system-overview.md` - Project goals and architecture
- `docs/02-hardware-setup.md` - Hardware requirements and setup
- `docs/03-software-architecture.md` - Technical design and data flow
- `docs/04-installation-guide.md` - Step-by-step installation
- `docs/05-alert-system.md` - Alert logic and speaker integration
- `docs/06-security-privacy.md` - Security best practices
- `docs/07-testing-verification.md` - Testing strategies
- `docs/08-timeline-milestones.md` - Project phases and timeline
- `docs/09-maintenance.md` - Maintenance and upgrade plans

## Project Structure
```
smart-cctv-system/
├── src/                    # Source code
│   ├── capture/           # Video stream capture
│   ├── detection/         # Object detection
│   ├── tracking/          # Movement tracking
│   ├── distance/          # Distance calculation
│   ├── alerts/            # Alert system
│   └── utils/             # Utilities
├── config/                # Configuration files
├── models/                # Pre-trained models
├── tests/                 # Test suite
├── docs/                  # Documentation
├── docker/                # Docker files
└── scripts/               # Utility scripts
```

## Technology Stack
- **Language**: Python 3.9+
- **Computer Vision**: OpenCV
- **Deep Learning**: TensorFlow Lite / PyTorch
- **Object Detection**: YOLO v8 / MobileNet SSD
- **Audio**: PyAudio, pyttsx3, PyBluez
- **Messaging**: MQTT (optional)
- **Containerization**: Docker
- **Monitoring**: Prometheus, Grafana (optional)

## Hardware Requirements
### Minimum (Old Laptop)
- CPU: Intel Core i5 (4th gen) or equivalent
- RAM: 8GB
- Storage: 50GB free space
- OS: Ubuntu 20.04 LTS / Windows 10 / macOS 10.15+
- Network: Wired Ethernet recommended

### Cameras
- 4x IP cameras with RTSP/HTTP stream support
- Resolution: 720p minimum (1080p recommended)
- Frame rate: 15-30 fps

## License
MIT License - Free for personal and commercial use

## Support
For issues and questions, see the documentation or open an issue.
