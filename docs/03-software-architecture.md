# Software Architecture and Data Flow

## 1. Technology Stack

### 1.1 Core Technologies

**Programming Language**: Python 3.9+
- Reason: Rich ecosystem for computer vision and ML
- Excellent library support
- Easy to maintain and extend
- Cross-platform compatibility

**Computer Vision**: OpenCV 4.8+
- Video stream handling
- Image preprocessing
- Basic operations (resize, crop, color conversion)
- Camera calibration
- Drawing annotations

**Deep Learning Framework**: PyTorch 2.0+ (Primary) + TensorFlow Lite 2.13+ (Alternative)
- **PyTorch**: For YOLO v8 models, flexible and performant
- **TensorFlow Lite**: For edge deployment, optimized inference
- Choice depends on model selection

**Object Detection Models**:
1. **YOLO v8** (You Only Look Once v8) - Recommended
   - Fast: 30+ FPS on modern hardware
   - Accurate: mAP 50-55%
   - Pretrained on COCO dataset (80 classes)
   - Model sizes: nano, small, medium, large, xlarge
   - License: AGPL-3.0 (free for personal use)

2. **MobileNet SSD** (Alternative)
   - Lightweight: Better for older hardware
   - Fast: 40+ FPS even on CPU
   - Less accurate than YOLO
   - TensorFlow Lite optimized

3. **EfficientDet** (Alternative)
   - Balance of speed and accuracy
   - Good for edge devices

**Object Tracking**: DeepSORT (Simple Online and Realtime Tracking with Deep Association Metric)
- Multi-object tracking
- Maintains unique IDs across frames
- Handles occlusions
- Open-source

**Distance Estimation**: Monocular depth estimation
- Camera calibration-based approach
- Or use MiDaS (Monocular Depth Estimation model)
- No additional hardware required

### 1.2 Supporting Libraries

**Audio Processing**:
- `pyttsx3` - Text-to-speech (offline, multi-platform)
- `gTTS` - Google Text-to-Speech (requires internet, better quality)
- `PyAudio` - Audio playback control
- `pydub` - Audio manipulation
- `PyBluez` - Bluetooth communication (Linux/Windows)

**Data Handling**:
- `numpy` - Numerical operations
- `pandas` - Data logging and analysis
- `opencv-python` - Image processing
- `Pillow` - Image handling

**Configuration**:
- `PyYAML` - YAML configuration files
- `python-dotenv` - Environment variables
- `jsonschema` - Config validation

**Logging and Monitoring**:
- `loguru` - Advanced logging
- `prometheus_client` - Metrics export
- `psutil` - System resource monitoring

**Web Interface** (Optional):
- `Flask` - Lightweight web framework
- `Flask-SocketIO` - Real-time updates
- `Jinja2` - HTML templates

**Utilities**:
- `imutils` - OpenCV convenience functions
- `scipy` - Scientific computing
- `requests` - HTTP requests

### 1.3 Development Tools

- `pytest` - Unit testing
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks
- `Docker` - Containerization

## 2. Software Architecture

### 2.1 Architectural Pattern

**Modular Pipeline Architecture** with **Event-Driven Components**

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN APPLICATION                       │
│                    (Orchestrator/Manager)                   │
└─────────────────────────────────────────────────────────────┘
         │
         ├── Configuration Manager
         ├── Resource Manager
         ├── Event Bus
         └── Monitoring
         │
    ┌────┴────┬─────────┬──────────┬──────────┬────────┐
    │         │         │          │          │        │
┌───▼───┐ ┌──▼───┐ ┌───▼────┐ ┌───▼───┐ ┌────▼───┐ ┌─▼────┐
│Capture│ │Detect│ │ Track  │ │Distance│ │ Alert  │ │  UI  │
│Module │ │Module│ │ Module │ │Module │ │ Module │ │Module│
└───────┘ └──────┘ └────────┘ └───────┘ └────────┘ └──────┘
```

### 2.2 Module Descriptions

#### 2.2.1 Capture Module (`src/capture/`)
**Responsibility**: Acquire video frames from cameras

**Components**:
- `camera_manager.py` - Manages multiple camera connections
- `rtsp_stream.py` - RTSP stream handler
- `frame_buffer.py` - Thread-safe frame buffer
- `camera_calibration.py` - Load/use calibration data

**Key Features**:
- Multi-threaded capture (one thread per camera)
- Auto-reconnection on stream failure
- Frame rate limiting
- Buffer management to prevent memory overflow
- Stream health monitoring

**Input**: Camera RTSP/HTTP URLs
**Output**: Frame objects with metadata (camera_id, timestamp, resolution)

#### 2.2.2 Detection Module (`src/detection/`)
**Responsibility**: Detect objects in frames

**Components**:
- `object_detector.py` - Main detection interface
- `yolo_detector.py` - YOLO v8 implementation
- `ssd_detector.py` - MobileNet SSD implementation
- `model_loader.py` - Load and manage models

**Key Features**:
- Model abstraction (easy to swap models)
- Batch processing for efficiency
- Confidence threshold filtering
- Non-maximum suppression (NMS)
- Class filtering (only detect relevant objects)

**Input**: Frame objects
**Output**: Detection objects (bounding boxes, classes, confidence scores)

#### 2.2.3 Tracking Module (`src/tracking/`)
**Responsibility**: Track objects across frames

**Components**:
- `object_tracker.py` - Main tracking interface
- `deepsort_tracker.py` - DeepSORT implementation
- `track_manager.py` - Manage track lifecycle

**Key Features**:
- Unique ID assignment
- Track association across frames
- Occlusion handling
- Track history maintenance
- Track filtering (age, hits)

**Input**: Detection objects per frame
**Output**: Track objects (ID, trajectory, age, class)

#### 2.2.4 Distance Module (`src/distance/`)
**Responsibility**: Calculate distance to objects

**Components**:
- `distance_calculator.py` - Main distance interface
- `monocular_depth.py` - Camera calibration-based method
- `midas_depth.py` - MiDaS model-based method (optional)
- `reference_manager.py` - Manage reference points

**Key Features**:
- Camera-specific calculations
- Reference point-based distance
- Metric conversion (pixels to meters)
- Distance to critical areas calculation

**Input**: Track objects with bounding boxes, camera calibration
**Output**: Distance measurements (meters)

#### 2.2.5 Alert Module (`src/alerts/`)
**Responsibility**: Trigger and deliver alerts

**Components**:
- `alert_manager.py` - Main alert orchestrator
- `rule_engine.py` - Evaluate alert rules
- `speaker_interface.py` - Abstract speaker interface
- `wired_speaker.py` - 3.5mm audio output
- `bluetooth_speaker.py` - Bluetooth audio output
- `tts_engine.py` - Text-to-speech synthesis
- `audio_player.py` - Audio playback

**Key Features**:
- Rule-based triggering
- Multi-speaker support
- Alert cooldown (prevent spam)
- Alert queue management
- Retry on failure

**Input**: Track objects with distances, alert rules
**Output**: Audio alerts via speakers

#### 2.2.6 UI Module (`src/ui/`) - Optional
**Responsibility**: Provide web interface

**Components**:
- `web_server.py` - Flask web server
- `dashboard.py` - Main dashboard
- `api.py` - REST API endpoints
- `templates/` - HTML templates
- `static/` - CSS, JS, images

**Key Features**:
- Live video feeds
- Real-time detection overlays
- Alert history
- System status
- Configuration editor

### 2.3 Core Classes and Interfaces

```python
# Frame data structure
@dataclass
class Frame:
    camera_id: str
    timestamp: float
    image: np.ndarray
    resolution: Tuple[int, int]
    frame_number: int

# Detection result
@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_name: str
    class_id: int
    confidence: float
    camera_id: str
    timestamp: float

# Track object
@dataclass
class Track:
    track_id: int
    detections: List[Detection]
    class_name: str
    trajectory: List[Tuple[int, int]]  # center points
    age: int
    hits: int
    time_since_update: int
    is_confirmed: bool

# Distance measurement
@dataclass
class DistanceMeasurement:
    track_id: int
    distance_to_camera: float
    distance_to_reference: Dict[str, float]  # e.g., {"front_door": 3.2}
    position_3d: Optional[Tuple[float, float, float]]

# Alert event
@dataclass
class AlertEvent:
    event_id: str
    trigger_time: float
    alert_type: str
    message: str
    track_id: int
    camera_id: str
    severity: str  # "low", "medium", "high", "critical"
    metadata: Dict[str, Any]
```

## 3. Data Flow Pipeline

### 3.1 End-to-End Data Flow

```
┌─────────────┐
│   Camera    │
│   Streams   │
└──────┬──────┘
       │ RTSP/HTTP
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: VIDEO CAPTURE                                        │
│ - Connect to camera streams                                  │
│ - Decode video frames                                        │
│ - Add to frame buffer                                        │
└──────┬──────────────────────────────────────────────────────┘
       │ Frame object (1920x1080 RGB)
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: PREPROCESSING                                        │
│ - Resize frame (640x640 for YOLO)                           │
│ - Normalize pixel values                                     │
│ - Convert color space if needed                              │
└──────┬──────────────────────────────────────────────────────┘
       │ Preprocessed frame (640x640)
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: OBJECT DETECTION                                     │
│ - Run inference (YOLO v8)                                    │
│ - Get bounding boxes + class + confidence                    │
│ - Filter by confidence threshold (>0.5)                      │
│ - Apply NMS (remove duplicate boxes)                         │
└──────┬──────────────────────────────────────────────────────┘
       │ List[Detection]
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: OBJECT TRACKING                                      │
│ - Match detections to existing tracks                        │
│ - Assign unique IDs                                          │
│ - Update trajectories                                        │
│ - Handle new/lost tracks                                     │
└──────┬──────────────────────────────────────────────────────┘
       │ List[Track]
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: DISTANCE CALCULATION                                 │
│ - For each "person" track:                                   │
│   - Calculate distance from camera (using calibration)       │
│   - Calculate distance to reference points (door, car)       │
│   - Store in DistanceMeasurement                             │
└──────┬──────────────────────────────────────────────────────┘
       │ List[Track + DistanceMeasurement]
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: ALERT RULE EVALUATION                                │
│ - Check each track against alert rules:                      │
│   - "Person within 5m of front door at night"                │
│   - "Person within 3m of vehicle"                            │
│   - "Unknown object loitering for 5 minutes"                 │
│ - If rule triggered → Create AlertEvent                      │
└──────┬──────────────────────────────────────────────────────┘
       │ List[AlertEvent]
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: ALERT DELIVERY                                       │
│ - Generate TTS audio message                                 │
│ - Send to speaker queue                                      │
│ - Play through wired or Bluetooth speaker                    │
│ - Log alert to database/file                                 │
└──────┬──────────────────────────────────────────────────────┘
       │ Alert delivered
       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: LOGGING & VISUALIZATION (Parallel)                   │
│ - Save snapshot with bounding boxes                          │
│ - Log event details to file                                  │
│ - Update web dashboard (if enabled)                          │
│ - Export metrics to Prometheus (if enabled)                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Threading Model

**Multi-threaded architecture for performance**:

```
┌──────────────────────────────────────────────────────────────┐
│                        Main Thread                           │
│  - Application orchestration                                 │
│  - Configuration management                                  │
│  - Resource cleanup                                          │
└──────────────────────────────────────────────────────────────┘
       │
       ├── Capture Threads (1 per camera)
       │   ├── Thread 1: Camera 1 (Front)
       │   ├── Thread 2: Camera 2 (Back)
       │   ├── Thread 3: Camera 3 (Side)
       │   └── Thread 4: Camera 4 (Garage)
       │
       ├── Processing Thread Pool (2-4 threads)
       │   ├── Worker 1: Detection + Tracking
       │   ├── Worker 2: Detection + Tracking
       │   ├── Worker 3: Distance Calculation
       │   └── Worker 4: Distance Calculation
       │
       ├── Alert Thread
       │   └── Alert evaluation and delivery
       │
       ├── Audio Playback Thread
       │   └── TTS generation and speaker output
       │
       └── UI Thread (Optional)
           └── Web server (Flask)
```

**Thread Communication**:
- `queue.Queue` - Thread-safe queues between stages
- `threading.Lock` - Protect shared resources
- `threading.Event` - Shutdown signaling

### 3.3 Data Storage

**Configuration Files** (YAML):
- `config/config.yaml` - Main configuration
- `config/cameras.yaml` - Camera definitions
- `config/alerts.yaml` - Alert rules
- `config/zones.yaml` - Reference points and zones

**Runtime Data**:
- **Logs**: `logs/app.log`, `logs/alerts.log`, `logs/errors.log`
- **Events**: `data/events.db` (SQLite database)
- **Snapshots**: `data/snapshots/YYYY-MM-DD/` (JPEG images)
- **Models**: `models/yolov8n.pt`, `models/deepsort.pth`
- **Calibration**: `config/calibration/camera_1.json`

**Database Schema** (SQLite):
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    camera_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    track_id INTEGER,
    class_name TEXT,
    distance REAL,
    alert_triggered INTEGER,
    snapshot_path TEXT,
    metadata TEXT  -- JSON
);

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    event_id INTEGER,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    delivered INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE tracks (
    track_id INTEGER PRIMARY KEY,
    first_seen REAL NOT NULL,
    last_seen REAL NOT NULL,
    camera_id TEXT NOT NULL,
    class_name TEXT NOT NULL,
    trajectory TEXT  -- JSON array of points
);
```

## 4. Model Selection and Configuration

### 4.1 YOLO v8 Model Variants

| Model | Size (MB) | mAP | Speed (FPS) | Use Case |
|-------|-----------|-----|-------------|----------|
| YOLOv8n | 6 | 37.3 | 45 | Old laptop, CPU-only |
| YOLOv8s | 22 | 44.9 | 35 | Balanced, recommended |
| YOLOv8m | 52 | 50.2 | 25 | GPU available |
| YOLOv8l | 87 | 52.9 | 18 | High accuracy needed |
| YOLOv8x | 136 | 53.9 | 12 | Max accuracy, GPU |

**Recommendation**: Start with **YOLOv8n** or **YOLOv8s**

### 4.2 Model Optimization

**Quantization** (Reduce model size and increase speed):
```python
# Post-training quantization
# FP32 → FP16: 2x faster, minimal accuracy loss
# FP32 → INT8: 4x faster, <3% accuracy loss
```

**TensorFlow Lite Conversion**:
```python
# Convert PyTorch → ONNX → TFLite
# Enables edge deployment
# Compatible with Coral Edge TPU
```

**ONNX Runtime**:
```python
# Alternative to PyTorch inference
# Often faster on CPU
# Multi-platform support
```

### 4.3 Model Download and Setup

**Automatic Download** (on first run):
```python
# YOLOv8 models auto-download from Ultralytics
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Downloads if not present
```

**Manual Download**:
```bash
# Download to models/ directory
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

## 5. Distance Calculation Methods

### 5.1 Method 1: Camera Calibration + Geometry (Recommended)

**Principle**: Use similar triangles and camera intrinsic parameters

**Requirements**:
- Camera calibration data (focal length, principal point)
- Known camera height and tilt angle
- Assumption: Objects on ground plane

**Formula**:
```
Distance (meters) = (Camera_Height * Focal_Length) / (Object_Bottom_Y * Pixel_Height)
```

**Pros**:
- Fast computation
- No additional models needed
- Accurate for ground-plane objects

**Cons**:
- Requires calibration per camera
- Less accurate for non-ground objects
- Assumes flat ground

**Calibration Script**: `scripts/calibrate_camera.py`

### 5.2 Method 2: Monocular Depth Estimation (MiDaS)

**Principle**: Use deep learning to estimate depth map

**Model**: MiDaS v3 (Intel)
- Pretrained on multiple datasets
- Outputs relative depth (not absolute)
- Requires scale calibration

**Pros**:
- Works for any object position
- No geometric assumptions
- Handles complex scenes

**Cons**:
- Slower (additional model inference)
- Relative depth (needs calibration for absolute)
- More GPU memory needed

**Implementation**: `src/distance/midas_depth.py`

### 5.3 Method 3: Stereo Vision (Future)

**Principle**: Use two cameras to calculate depth

**Requirements**:
- Second camera at each location
- Camera synchronization
- Stereo calibration

**Pros**:
- Most accurate
- True 3D reconstruction

**Cons**:
- Requires additional cameras
- Complex calibration
- Higher computational cost

**Status**: Not in MVP, future enhancement

## 6. Alert System Logic

### 6.1 Alert Rules

**Rule Structure** (YAML):
```yaml
alert_rules:
  - name: "Night Intruder Detection"
    enabled: true
    priority: critical
    conditions:
      - camera_id: ["camera_1", "camera_2"]  # Front and back
      - time_range: ["22:00", "06:00"]       # Night time
      - object_class: "person"
      - distance_to_reference:
          reference: "front_door"
          operator: "less_than"
          value: 5.0                          # 5 meters
    actions:
      - type: "audio_alert"
        message: "Warning! Person detected near entrance at night."
        speaker: ["bedroom", "living_room"]
      - type: "snapshot"
      - type: "log"
        severity: "critical"
    cooldown: 60  # seconds between repeated alerts

  - name: "Vehicle Proximity"
    enabled: true
    priority: high
    conditions:
      - camera_id: "camera_4"
      - object_class: "person"
      - distance_to_reference:
          reference: "car"
          operator: "less_than"
          value: 3.0
    actions:
      - type: "audio_alert"
        message: "Alert: Person detected near your vehicle."
        speaker: "living_room"
      - type: "snapshot"
    cooldown: 30

  - name: "Package Delivery"
    enabled: true
    priority: low
    conditions:
      - camera_id: "camera_1"
      - sequence:
          - object_class: "person"
            duration: 10  # Present for 10 seconds
          - object_class: "person"
            action: "leaves"
          - object_class: "unknown"  # Package left behind
            duration: 5
    actions:
      - type: "audio_alert"
        message: "Package delivered at front door."
        speaker: "all"
      - type: "snapshot"
    cooldown: 300  # 5 minutes
```

### 6.2 Rule Evaluation Engine

**Process**:
1. For each frame, check all active tracks
2. Evaluate each enabled rule against each track
3. Check all conditions (AND logic within rule)
4. If all conditions met → Trigger alert
5. Check cooldown period (don't spam)
6. Execute actions (audio, snapshot, log)
7. Update rule state (last_triggered time)

**Optimization**:
- Rules indexed by camera_id
- Only evaluate relevant rules per camera
- Cache rule evaluations for 1 second

## 7. Audio Alert Implementation

### 7.1 Text-to-Speech (TTS)

**Option 1: pyttsx3** (Offline, Recommended)
```python
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed
engine.setProperty('volume', 0.9)  # Volume
engine.say("Warning! Person detected near entrance.")
engine.runAndWait()
```

**Pros**: Offline, fast, no API limits
**Cons**: Robotic voice quality

**Option 2: gTTS** (Google TTS)
```python
from gtts import gTTS
import os

tts = gTTS(text="Warning! Person detected.", lang='en')
tts.save("alert.mp3")
os.system("mpg321 alert.mp3")  # Or use PyAudio
```

**Pros**: Better voice quality
**Cons**: Requires internet, rate limits

**Hybrid Approach**:
- Pre-generate common alert messages
- Cache audio files
- Use pyttsx3 for dynamic messages

### 7.2 Wired Speaker Output

**Using PyAudio**:
```python
import pyaudio
import wave

def play_audio(filename):
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    
    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True
    )
    
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
```

**System Audio**:
```python
# Alternative: Use system audio player
import os
os.system("aplay alert.wav")  # Linux
os.system("afplay alert.wav")  # macOS
os.system("start alert.wav")  # Windows
```

### 7.3 Bluetooth Speaker Output

**Using PyBluez** (Linux):
```python
import bluetooth

def find_bluetooth_speaker():
    nearby_devices = bluetooth.discover_devices(lookup_names=True)
    for addr, name in nearby_devices:
        if "speaker" in name.lower():
            return addr
    return None

def connect_bluetooth_speaker(address):
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((address, 1))  # RFCOMM port 1
    return sock
```

**Using BlueALSA** (Linux):
```bash
# Setup BlueALSA service
sudo apt-get install bluealsa
```

**Auto-Reconnect Logic**:
```python
def ensure_speaker_connected():
    if not is_speaker_connected():
        reconnect_speaker()
        time.sleep(2)  # Wait for connection
    return is_speaker_connected()
```

**Windows Bluetooth**:
```python
# Use Windows Bluetooth API via pybluez or system audio
```

### 7.4 Multi-Speaker Support

**Speaker Manager**:
```python
class SpeakerManager:
    def __init__(self):
        self.speakers = {
            'bedroom': WiredSpeaker(device_id=0),
            'living_room': BluetoothSpeaker(mac='AA:BB:CC:DD:EE:FF'),
            'all': [WiredSpeaker(), BluetoothSpeaker()]
        }
    
    def play_alert(self, message, speaker_name='all'):
        audio_file = self.tts_engine.generate(message)
        speakers = self.speakers.get(speaker_name, [])
        for speaker in speakers:
            speaker.play(audio_file)
```

## 8. Web Dashboard (Optional)

### 8.1 Dashboard Features

- **Live View**: Real-time video feeds with detection overlays
- **Alert History**: Searchable table of past alerts
- **System Status**: CPU, memory, FPS, camera health
- **Configuration**: Edit alert rules and settings
- **Logs**: View application logs

### 8.2 Technology

**Backend**: Flask + Flask-SocketIO
**Frontend**: HTML5, CSS3, JavaScript (Vanilla or Vue.js)
**Real-time**: WebSockets for live updates

### 8.3 API Endpoints

```
GET  /api/cameras          - List cameras and status
GET  /api/cameras/<id>/feed - Video stream (MJPEG)
GET  /api/alerts           - Alert history (paginated)
GET  /api/events           - Detection events
GET  /api/stats            - System statistics
POST /api/alerts/test      - Test alert system
GET  /api/config           - Get configuration
PUT  /api/config           - Update configuration
GET  /api/logs             - Application logs
```

## 9. Configuration Management

### 9.1 Configuration Files

**Main Config** (`config/config.yaml`):
```yaml
system:
  name: "Home CCTV System"
  log_level: "INFO"
  data_dir: "./data"
  models_dir: "./models"

processing:
  detection:
    model: "yolov8n"
    device: "cpu"  # or "cuda:0"
    confidence_threshold: 0.5
    nms_threshold: 0.4
    input_size: [640, 640]
    classes_filter: ["person", "car", "truck", "dog", "cat"]
  
  tracking:
    max_age: 30
    min_hits: 3
    iou_threshold: 0.3
  
  distance:
    method: "calibration"  # or "midas"
    unit: "meters"

performance:
  fps_limit: 15
  frame_skip: 0
  batch_size: 1
  thread_pool_size: 4

storage:
  events_retention_days: 30
  snapshots_retention_days: 7
  log_rotation_mb: 100
  database_path: "./data/events.db"

ui:
  enabled: false
  host: "0.0.0.0"
  port: 5000
  auth_enabled: true
  username: "admin"
  password_hash: "..."
```

**Camera Config** (`config/cameras.yaml`):
```yaml
cameras:
  - id: "camera_1"
    name: "Front Door"
    url: "rtsp://admin:password@192.168.1.101:554/stream1"
    location: "front_entrance"
    enabled: true
    fps: 25
    calibration_file: "config/calibration/camera_1.json"
    reference_points:
      - name: "front_door"
        position: [1920, 1080]  # pixel coordinates
        real_distance: 3.0      # meters from camera
    zones:
      - name: "entrance_zone"
        polygon: [[100, 100], [500, 100], [500, 400], [100, 400]]
        type: "critical"
  
  - id: "camera_2"
    name: "Backyard"
    url: "rtsp://admin:password@192.168.1.102:554/stream1"
    location: "back_yard"
    enabled: true
    fps: 25
    calibration_file: "config/calibration/camera_2.json"
  
  # ... camera_3, camera_4
```

**Alert Rules** (`config/alerts.yaml`):
See section 6.1 for structure.

### 9.2 Configuration Validation

**JSON Schema validation**:
```python
import jsonschema
import yaml

with open('config/config.schema.json') as f:
    schema = json.load(f)

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

jsonschema.validate(config, schema)  # Raises error if invalid
```

## 10. Error Handling and Recovery

### 10.1 Error Categories

**Camera Errors**:
- Connection lost: Auto-reconnect every 10 seconds
- Stream timeout: Restart capture thread
- Invalid frames: Log and skip

**Model Errors**:
- Model loading failure: Exit with error
- Inference error: Log and skip frame
- OOM error: Reduce batch size

**Alert Errors**:
- TTS failure: Fall back to pre-recorded audio
- Speaker connection lost: Retry 3 times, then log
- Audio playback error: Log and continue

**System Errors**:
- Disk full: Delete old snapshots
- Memory leak: Monitor and restart if needed
- CPU overload: Reduce FPS or skip frames

### 10.2 Recovery Strategies

```python
@retry(max_attempts=3, delay=5)
def connect_camera(url):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        raise ConnectionError(f"Failed to open {url}")
    return cap

def graceful_shutdown(signal_received, frame):
    logger.info("Shutting down gracefully...")
    # Stop all threads
    # Close camera connections
    # Save state
    # Close database
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
```

## 11. Performance Optimization

### 11.1 Optimization Techniques

**Frame Skipping**:
```python
# Process every Nth frame
if frame_count % 2 == 0:  # Process every 2nd frame
    detections = detector.detect(frame)
```

**ROI Processing**:
```python
# Only process regions of interest
roi = frame[100:900, 200:1800]
detections = detector.detect(roi)
```

**Model Quantization**:
```python
# Use INT8 quantized models (4x faster)
model = YOLO('yolov8n-int8.tflite')
```

**Batch Processing**:
```python
# Process multiple frames together
frames = [frame1, frame2, frame3, frame4]
detections = detector.detect_batch(frames)
```

**Multi-Processing**:
```python
# Use multiple processes for parallel processing
from multiprocessing import Pool
with Pool(processes=4) as pool:
    results = pool.map(process_frame, frames)
```

### 11.2 Resource Limits

**CPU**:
- Set thread affinity to specific cores
- Use `nice` to lower priority

**Memory**:
- Limit frame buffer size
- Clear old track history
- Garbage collection tuning

**Disk**:
- Automatic cleanup of old data
- Compress snapshots
- Rotate logs

## 12. Monitoring and Logging

### 12.1 Logging Strategy

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages (non-critical issues)
- ERROR: Error messages (failures)
- CRITICAL: Critical errors (system failure)

**Log Files**:
```
logs/
├── app.log           # Main application log
├── alerts.log        # Alert-specific log
├── errors.log        # Error log only
├── performance.log   # FPS, latency metrics
└── archived/         # Old logs (compressed)
```

**Log Format**:
```
2025-10-24 14:32:15.123 | INFO     | capture | camera_1 | Connected to front door camera
2025-10-24 14:32:16.456 | WARNING  | detection | camera_1 | Low confidence detection: 0.42
2025-10-24 14:32:20.789 | CRITICAL | alert | camera_1 | Person detected near entrance!
```

### 12.2 Metrics Collection

**Prometheus Metrics** (Optional):
```python
from prometheus_client import Counter, Gauge, Histogram

# Metrics
frames_processed = Counter('frames_processed_total', 'Total frames processed', ['camera'])
detections_count = Counter('detections_total', 'Total detections', ['camera', 'class'])
processing_time = Histogram('processing_time_seconds', 'Processing time', ['stage'])
cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('memory_usage_mb', 'Memory usage in MB')

# Export endpoint
from prometheus_client import start_http_server
start_http_server(8000)  # Metrics at http://localhost:8000/metrics
```

**Grafana Dashboard** (Optional):
- Visualize metrics over time
- Alert on anomalies
- Monitor system health

## 13. Scalability Considerations

### 13.1 Horizontal Scaling

**Add More Cameras**:
- Simply add camera config to `cameras.yaml`
- System auto-detects and starts capture thread
- Consider hardware limits (CPU, network)

**Distributed Processing**:
```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Camera 1 │───>│ Server 1 │───>│          │
│ Camera 2 │    └──────────┘    │  Central │
├──────────┤                     │  Alert   │
│ Camera 3 │───>│ Server 2 │───>│  Server  │
│ Camera 4 │    └──────────┘    │          │
└──────────┘                     └──────────┘
```

**MQTT Message Broker**:
- Cameras publish frames to MQTT topics
- Processing nodes subscribe and process
- Alert server subscribes to detection events

### 13.2 Vertical Scaling

**Hardware Upgrades**:
- Add GPU (NVIDIA, Intel, AMD)
- More RAM (16GB → 32GB)
- Faster CPU (8-core, higher clock)
- Edge TPU (Coral USB Accelerator)

**Software Optimization**:
- Use TensorFlow Lite + Edge TPU
- Enable GPU acceleration
- Optimize model (quantization)
- Parallel processing

### 13.3 Cloud Integration (Future)

**Hybrid Approach**:
- Local processing for real-time alerts
- Cloud storage for long-term retention
- Cloud analytics for behavior patterns
- Cloud backup for disaster recovery

**Cloud Services**:
- AWS: S3 (storage), Lambda (processing), IoT Core (messaging)
- Azure: Blob Storage, Functions, IoT Hub
- Google Cloud: Cloud Storage, Cloud Functions, Pub/Sub

**Privacy Considerations**:
- Encrypt data before cloud upload
- Use anonymization (blur faces)
- Comply with data privacy laws

## 14. Security Architecture

See `docs/06-security-privacy.md` for detailed security implementation.

**Key Points**:
- All local processing (no cloud by default)
- Encrypted configuration files
- Password-protected web interface
- Camera credentials securely stored
- Network isolation (VLAN)
- Regular security updates

## 15. Development Workflow

### 15.1 Development Setup

```bash
# Clone repository
git clone <repo_url>
cd smart-cctv-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8 src/
black src/
mypy src/

# Start development server
python src/main.py --config config/config.yaml
```

### 15.2 Testing Strategy

**Unit Tests**: Test individual functions and classes
**Integration Tests**: Test module interactions
**End-to-End Tests**: Test full pipeline with recorded video
**Performance Tests**: Benchmark FPS, latency, resource usage

### 15.3 CI/CD (Future)

- GitHub Actions or GitLab CI
- Automated testing on commit
- Docker image building
- Automated deployment

## 16. Deployment Options

### 16.1 Bare Metal (Recommended for MVP)

```bash
# Direct installation on laptop
python src/main.py
```

### 16.2 Docker Container

```bash
# Build image
docker build -t smart-cctv:latest .

# Run container
docker run -d \
  --name smart-cctv \
  --restart unless-stopped \
  -v ./config:/app/config \
  -v ./data:/app/data \
  -v ./models:/app/models \
  --network host \
  smart-cctv:latest
```

### 16.3 Systemd Service (Linux)

```bash
# Install as system service
sudo cp scripts/smart-cctv.service /etc/systemd/system/
sudo systemctl enable smart-cctv
sudo systemctl start smart-cctv
```

Auto-starts on boot, auto-restarts on crash.

## 17. Software Architecture Summary

This architecture provides:
- ✅ Modular design (easy to extend)
- ✅ Scalable (4 → 8+ cameras)
- ✅ Performant (optimized for old hardware)
- ✅ Reliable (error handling, auto-recovery)
- ✅ Maintainable (clear separation of concerns)
- ✅ Configurable (no code changes needed)
- ✅ Open-source (all free tools)

**Next Steps**: Implementation of core modules (see next documentation sections).
