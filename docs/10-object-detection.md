# Object Detection Module Documentation

## Overview

The `object_detector.py` module provides YOLO v8-based object detection capabilities for the Smart CCTV system. It can detect humans, vehicles, animals, and other objects in real-time video streams.

## Features

### 🎯 **Supported Objects**
- **Humans**: Person detection with high accuracy
- **Vehicles**: Car, truck, motorcycle, bus, bicycle
- **Animals**: Dog, cat, bird, and other animals
- **Objects**: Backpack, suitcase, handbag, umbrella

### 🚀 **Performance**
- **Real-time processing**: 15-100+ FPS depending on model size
- **Multiple devices**: CPU, CUDA GPU, Apple MPS
- **Configurable models**: YOLOv8n (fastest) to YOLOv8l (most accurate)
- **Memory efficient**: Optimized for running on old laptops

### ⚙️ **Configuration**
All detection parameters are configurable via `config.yaml`:

```yaml
processing:
  detection:
    model: "yolov8n"  # yolov8n, yolov8s, yolov8m, yolov8l
    device: "cpu"     # cpu, cuda:0, mps
    confidence_threshold: 0.5
    nms_threshold: 0.4
    input_size: [640, 640]
    classes_filter: ["person", "car", "truck", "motorcycle", "dog", "cat"]
    batch_size: 1
```

## API Reference

### ObjectDetector Class

#### `__init__(config)`
Initialize the detector with configuration.

**Parameters:**
- `config`: Configuration object containing detection settings

**Example:**
```python
from detection.object_detector import ObjectDetector
from utils.config_loader import ConfigLoader

config = ConfigLoader("config/config.yaml")
detector = ObjectDetector(config)
```

#### `detect(frame) -> List[Detection]`
Detect objects in a video frame.

**Parameters:**
- `frame`: Frame object containing image data

**Returns:**
- List of Detection objects

**Example:**
```python
detections = detector.detect(frame)
for detection in detections:
    print(f"{detection.class_name}: {detection.confidence:.2f}")
```

#### `detect_and_draw(frame, draw_confidence=True, draw_labels=True) -> np.ndarray`
Detect objects and draw bounding boxes on the image.

**Parameters:**
- `frame`: Frame object
- `draw_confidence`: Whether to show confidence scores
- `draw_labels`: Whether to show class labels

**Returns:**
- Annotated image as numpy array

**Example:**
```python
annotated_image = detector.detect_and_draw(frame)
cv2.imshow("Detections", annotated_image)
```

#### Helper Methods

```python
# Get specific object types
humans = detector.get_human_detections(detections)
vehicles = detector.get_vehicle_detections(detections)
dogs = detector.get_detections_by_class(detections, "dog")
```

### Detection Class

The `Detection` dataclass contains detection results:

```python
@dataclass
class Detection:
    bbox: tuple          # (x1, y1, x2, y2) bounding box
    confidence: float    # Detection confidence (0.0-1.0)
    class_id: int       # COCO class ID
    class_name: str     # Human-readable class name
    center_point: tuple # (x, y) center coordinates
    area: float         # Bounding box area in pixels
```

**Example Usage:**
```python
for detection in detections:
    x1, y1, x2, y2 = detection.bbox
    cx, cy = detection.center_point
    print(f"Found {detection.class_name} at ({cx}, {cy}) with {detection.confidence:.2f} confidence")
```

## Model Information

### YOLO v8 Model Variants

| Model | Size | Speed (CPU) | Accuracy | Use Case |
|-------|------|-------------|----------|----------|
| **yolov8n** | 6MB | ~100 FPS | Good | Real-time, resource-constrained |
| **yolov8s** | 22MB | ~60 FPS | Better | Balanced speed/accuracy |
| **yolov8m** | 52MB | ~30 FPS | High | Higher accuracy needs |
| **yolov8l** | 87MB | ~20 FPS | Highest | Maximum accuracy |

### Supported Classes

The detector supports 80+ COCO classes, but filters to security-relevant objects by default:

**Priority Classes (Security):**
- `person` - Human detection
- `car`, `truck`, `bus` - Vehicles
- `motorcycle`, `bicycle` - Two-wheelers  
- `dog`, `cat` - Pets/animals

**All Available Classes:**
See `COCO_CLASSES` dictionary in the code for complete list.

## Integration Examples

### 1. Basic Detection Loop

```python
# Main processing loop
while running:
    frames = camera_manager.get_frames()
    
    for frame in frames:
        # Detect objects
        detections = detector.detect(frame)
        
        # Process humans
        humans = detector.get_human_detections(detections)
        for human in humans:
            distance = distance_calc.calculate(human, frame.camera_id)
            if distance < 5.0:  # Within 5 meters
                alert_manager.trigger_alert("Person near entrance")
```

### 2. Alert System Integration

```python
# In alert_manager.py
def evaluate_detections(self, detections, frame):
    humans = self.detector.get_human_detections(detections)
    vehicles = self.detector.get_vehicle_detections(detections)
    
    # Check night intruder rule
    if self.is_night_time() and humans:
        for human in humans:
            if self.is_near_entrance(human, frame.camera_id):
                self.trigger_alert("Night intruder detected!")
    
    # Check vehicle proximity
    if vehicles and humans:
        for human, vehicle in zip(humans, vehicles):
            if self.distance_between(human, vehicle) < 3.0:
                self.trigger_alert("Person near vehicle!")
```

### 3. Performance Monitoring

```python
import time

start_time = time.time()
detections = detector.detect(frame)
inference_time = time.time() - start_time

print(f"Detected {len(detections)} objects in {inference_time:.3f}s")
print(f"FPS: {1.0/inference_time:.1f}")
```

## Configuration Tuning

### For Best Performance (Speed)
```yaml
processing:
  detection:
    model: "yolov8n"
    confidence_threshold: 0.6  # Higher = fewer false positives
    input_size: [416, 416]     # Smaller = faster
    classes_filter: ["person", "car"]  # Fewer classes
```

### For Best Accuracy
```yaml
processing:
  detection:
    model: "yolov8l"
    confidence_threshold: 0.3  # Lower = more detections
    input_size: [640, 640]     # Larger = more accurate
    classes_filter: []         # All classes
```

### For Old Laptops
```yaml
processing:
  detection:
    model: "yolov8n"
    device: "cpu"
    confidence_threshold: 0.7
    input_size: [320, 320]     # Very small for speed
performance:
  fps_limit: 10              # Limit processing rate
  frame_skip: 1              # Skip every other frame
```

## Installation & Dependencies

### System Requirements

**Linux/Ubuntu:**
```bash
# Install system dependencies for PyAudio and OpenCV
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
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install portaudio
brew install ffmpeg
```

**Windows:**
```bash
# PyAudio pre-compiled wheels are available for Windows
# No additional system dependencies needed
```

### Python Dependencies

**Option 1: Full Installation**
```bash
pip install -r requirements.txt
```

**Option 2: Minimal Installation (Detection Only)**
```bash
# Core detection dependencies (no audio alerts)
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
pip install torch>=2.0.0
pip install torchvision>=0.15.0
pip install ultralytics>=8.0.0
pip install loguru>=0.7.0
pip install PyYAML>=6.0
pip install Pillow>=10.0.0
```

**Option 3: Docker Installation**
```bash
# Use pre-built Docker image (recommended for production)
docker-compose up --build
```

### Troubleshooting PyAudio Installation

**Issue: PyAudio build fails with "gcc failed: No such file or directory"**

**Linux Solution:**
```bash
# Install build tools and audio libraries
sudo apt-get install build-essential portaudio19-dev python3-dev

# Then install PyAudio
pip install PyAudio
```

**Alternative: Use system PyAudio**
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyaudio

# Or use conda instead of pip
conda install pyaudio
```

**macOS Solution:**
```bash
# Install portaudio first
brew install portaudio

# Set environment variables for compilation
export CPPFLAGS=-I/opt/homebrew/include
export LDFLAGS=-L/opt/homebrew/lib

# Then install PyAudio
pip install PyAudio
```

**Docker Solution (Recommended):**
```dockerfile
# Use the provided Dockerfile which handles all dependencies
docker build -t smart-cctv .
docker run -it --device=/dev/video0 smart-cctv
```

## Testing

### Prerequisites Check
```bash
# Verify core dependencies are installed
python -c "import cv2, torch, ultralytics; print('✓ Core dependencies OK')"

# Optional: Check audio dependencies
python -c "import pyaudio, pyttsx3; print('✓ Audio dependencies OK')" || echo "⚠ Audio features disabled"
```

### Test on Webcam
```bash
python scripts/test_detection.py --webcam --duration 60
```

### Test on Image
```bash
python scripts/test_detection.py --image path/to/test_image.jpg
```

### Run Example
```bash
python scripts/detector_example.py
```

## Troubleshooting

### Common Issues

**1. ImportError: No module named 'ultralytics'**
```bash
pip install ultralytics
```

**2. CUDA out of memory**
```yaml
# Switch to CPU or smaller model
processing:
  detection:
    device: "cpu"
    model: "yolov8n"
```

**3. Low FPS**
```yaml
# Optimize for speed
processing:
  detection:
    model: "yolov8n"
    input_size: [416, 416]
    confidence_threshold: 0.7
performance:
  fps_limit: 15
  frame_skip: 1
```

**4. Too many false positives**
```yaml
# Increase confidence threshold
processing:
  detection:
    confidence_threshold: 0.7  # Increase from 0.5
```

### Performance Benchmarks

**Hardware**: Intel i5-8250U (4 cores), 8GB RAM

| Model | Input Size | CPU FPS | GPU FPS | Memory |
|-------|------------|---------|---------|---------|
| yolov8n | 640x640 | 45 FPS | 120 FPS | 2GB |
| yolov8n | 416x416 | 78 FPS | 180 FPS | 1.5GB |
| yolov8s | 640x640 | 28 FPS | 85 FPS | 3GB |

## Security Considerations

### Privacy
- All processing happens locally
- No data sent to external servers
- YOLO model downloaded once, cached locally

### Accuracy
- Test detection accuracy on your specific cameras
- Adjust confidence thresholds based on your environment
- Consider lighting conditions (day/night performance)

### Resources
- Monitor CPU/memory usage
- Set appropriate FPS limits
- Use frame skipping for resource-constrained systems

## Future Enhancements

1. **Custom Training**: Train YOLO on your specific environment
2. **Face Recognition**: Add face detection/recognition module
3. **Action Recognition**: Detect suspicious behaviors
4. **Tracking Integration**: Combine with object tracking for better performance
5. **Edge TPU**: Support for Google Coral Edge TPU acceleration

## Related Files

- `src/detection/object_detector.py` - Main implementation
- `src/tracking/object_tracker.py` - Object tracking module
- `src/distance/distance_calculator.py` - Distance calculation
- `src/alerts/alert_manager.py` - Alert system
- `scripts/test_detection.py` - Testing utilities
- `config/config.example.yaml` - Configuration examples