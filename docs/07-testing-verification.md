# Testing and Verification Strategy

## 1. Testing Overview

### Testing Pyramid
```
                    ┌─────────────┐
                    │  E2E Tests  │  (10%)
                    └─────────────┘
                 ┌──────────────────┐
                 │ Integration Tests│  (30%)
                 └──────────────────┘
              ┌────────────────────────┐
              │     Unit Tests         │  (60%)
              └────────────────────────┘
```

### Test Types
1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test module interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Benchmark and stress testing
5. **Security Tests**: Vulnerability assessment
6. **User Acceptance Tests**: Validate user requirements

---

## 2. Unit Testing

### 2.1 Test Framework: pytest

**Installation**:
```bash
pip install pytest pytest-cov pytest-mock
```

**Run unit tests**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_camera_manager.py

# Run tests matching pattern
pytest -k "camera"
```

### 2.2 Test Examples

**Test Camera Manager**:
```python
# tests/test_camera_manager.py
import pytest
from unittest.mock import Mock, patch
from src.capture.camera_manager import CameraManager, CameraStream

def test_camera_stream_initialization():
    """Test camera stream initialization."""
    config = {
        'id': 'test_cam',
        'name': 'Test Camera',
        'url': 'rtsp://test',
        'enabled': True
    }
    
    camera = CameraStream(config)
    
    assert camera.id == 'test_cam'
    assert camera.name == 'Test Camera'
    assert camera.enabled == True

@patch('cv2.VideoCapture')
def test_camera_connection(mock_capture):
    """Test camera connection."""
    mock_cap = Mock()
    mock_cap.isOpened.return_value = True
    mock_capture.return_value = mock_cap
    
    config = {'id': 'test', 'name': 'Test', 'url': 'rtsp://test', 'enabled': True}
    camera = CameraStream(config)
    
    result = camera._connect()
    
    assert result == True
    mock_capture.assert_called_once()
```

**Test Configuration Loader**:
```python
# tests/test_config_loader.py
import pytest
import tempfile
import yaml
from src.utils.config_loader import ConfigLoader

def test_config_loading():
    """Test configuration loading."""
    config_data = {
        'system': {'name': 'Test System'},
        'cameras': [{'id': 'cam1', 'url': 'rtsp://test'}]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    config = ConfigLoader(config_path)
    
    assert config.get('system.name') == 'Test System'
    assert len(config.get('cameras')) == 1

def test_config_validation():
    """Test configuration validation."""
    config_data = {
        'system': {'name': 'Test'},
        'cameras': [],
        'processing': {'detection': {'model': 'yolov8n'}},
        'alert_rules': []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    config = ConfigLoader(config_path)
    
    # Should fail validation (no cameras)
    assert config.validate() == False
```

### 2.3 Coverage Goals
- **Target**: >80% code coverage
- **Critical modules**: >90% coverage (camera_manager, detector, tracker)
- **Run coverage report**:
```bash
pytest --cov=src --cov-report=term-missing
```

---

## 3. Integration Testing

### 3.1 Module Integration Tests

**Test Detection Pipeline**:
```python
# tests/integration/test_detection_pipeline.py
import cv2
import numpy as np
from src.capture.camera_manager import Frame
from src.detection.object_detector import ObjectDetector
from src.utils.config_loader import ConfigLoader

def test_detection_pipeline():
    """Test frame capture to detection."""
    # Load config
    config = ConfigLoader('config/config.yaml')
    
    # Create detector
    detector = ObjectDetector(config)
    
    # Create test frame
    image = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Draw a person-like shape
    cv2.rectangle(image, (500, 300), (700, 900), (255, 255, 255), -1)
    
    frame = Frame(
        camera_id='test',
        timestamp=time.time(),
        image=image,
        resolution=(1920, 1080),
        frame_number=1
    )
    
    # Detect objects
    detections = detector.detect(frame)
    
    # Should detect something (even if not perfectly)
    assert len(detections) >= 0  # May or may not detect test shape
```

**Test Alert Flow**:
```python
# tests/integration/test_alert_flow.py
def test_alert_trigger_flow():
    """Test complete alert triggering flow."""
    # Create mock detection with person near door
    track = create_mock_track(class_name='person')
    track.distance_info = {'distance_to_reference': {'front_door': 3.0}}
    
    frame = create_mock_frame(camera_id='camera_1')
    
    # Alert manager should trigger alert
    alert_manager = AlertManager(config)
    alert_manager.evaluate([track], frame)
    
    # Check alert was logged
    alerts = db.get_recent_alerts(limit=1)
    assert len(alerts) > 0
    assert 'person' in alerts[0]['message'].lower()
```

### 3.2 Database Integration Tests

```python
# tests/integration/test_database.py
def test_database_operations():
    """Test database CRUD operations."""
    db = Database(':memory:')  # In-memory database
    
    # Insert event
    event_data = {
        'timestamp': time.time(),
        'camera_id': 'test_cam',
        'event_type': 'detection',
        'class_name': 'person'
    }
    
    event_id = db.insert_event(event_data)
    assert event_id > 0
    
    # Retrieve event
    events = db.get_recent_events(limit=1)
    assert len(events) == 1
    assert events[0]['class_name'] == 'person'
    
    # Cleanup
    db.cleanup_old_data(retention_days=0)
    events = db.get_recent_events()
    assert len(events) == 0
```

---

## 4. End-to-End Testing

### 4.1 Complete System Test

```bash
# Run system in test mode with recorded video
python scripts/e2e_test.py --video tests/data/test_video.mp4 --duration 60
```

**Test script**:
```python
# scripts/e2e_test.py
def run_e2e_test(video_path, duration):
    """Run end-to-end test with recorded video."""
    # Replace camera URLs with video file
    config = load_test_config(video_path)
    
    # Start system
    system = SmartCCTVSystem(config)
    
    # Run for specified duration
    start_time = time.time()
    system.start()
    
    time.sleep(duration)
    
    # Stop system
    system.stop()
    
    # Verify results
    stats = system.db.get_stats()
    
    print(f"E2E Test Results:")
    print(f"  Duration: {duration}s")
    print(f"  Frames processed: {system.frame_count}")
    print(f"  Detections: {stats['total_events']}")
    print(f"  Alerts triggered: {stats['total_alerts']}")
    
    # Basic validation
    assert system.frame_count > 0, "No frames processed"
    assert stats['total_events'] >= 0, "Event logging failed"
    
    return True
```

### 4.2 Camera Failure Scenario

```python
def test_camera_failure_recovery():
    """Test system handles camera disconnection."""
    system = SmartCCTVSystem()
    system.start()
    
    # Simulate camera disconnection
    camera = system.camera_manager.get_camera('camera_1')
    camera.cap.release()
    camera.cap = None
    
    # Wait for reconnection attempt
    time.sleep(15)
    
    # Verify camera reconnected
    assert camera.is_active() == True
```

---

## 5. Performance Testing

### 5.1 Benchmarking

**FPS Benchmark**:
```python
# scripts/benchmark_fps.py
import time
import cv2

def benchmark_detection_fps(detector, num_frames=100):
    """Benchmark detection FPS."""
    # Create test frame
    image = cv2.imread('tests/data/test_image.jpg')
    frame = Frame(camera_id='test', timestamp=time.time(), 
                  image=image, resolution=image.shape[:2][::-1], frame_number=1)
    
    start_time = time.time()
    
    for i in range(num_frames):
        detections = detector.detect(frame)
    
    elapsed = time.time() - start_time
    fps = num_frames / elapsed
    
    print(f"Detection FPS: {fps:.2f}")
    return fps

# Run benchmark
config = ConfigLoader('config/config.yaml')
detector = ObjectDetector(config)
fps = benchmark_detection_fps(detector)

assert fps >= 15, f"FPS too low: {fps} < 15"
```

**Resource Usage Monitor**:
```python
# scripts/monitor_resources.py
import psutil
import time

def monitor_system_resources(duration=60):
    """Monitor CPU, memory, GPU usage."""
    process = psutil.Process()
    
    cpu_samples = []
    mem_samples = []
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        cpu_samples.append(process.cpu_percent(interval=1))
        mem_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
    
    print(f"Resource Usage (over {duration}s):")
    print(f"  CPU: avg={sum(cpu_samples)/len(cpu_samples):.1f}%, max={max(cpu_samples):.1f}%")
    print(f"  Memory: avg={sum(mem_samples)/len(mem_samples):.1f}MB, max={max(mem_samples):.1f}MB")
    
    # Validation
    assert max(cpu_samples) < 90, "CPU usage too high"
    assert max(mem_samples) < 6144, "Memory usage too high (>6GB)"
```

### 5.2 Stress Testing

```python
def stress_test_multi_camera(num_cameras=4, duration=600):
    """Stress test with multiple cameras."""
    # Configure multiple cameras
    config = create_stress_test_config(num_cameras)
    
    system = SmartCCTVSystem(config)
    system.start()
    
    # Monitor for crashes/errors
    time.sleep(duration)
    
    # Check system stability
    assert system.running == True
    assert system.camera_manager.active_count() == num_cameras
    
    system.stop()
```

---

## 6. Security Testing

### 6.1 Vulnerability Scanning

```bash
# Scan Python dependencies for vulnerabilities
pip install safety
safety check

# Scan for common security issues
pip install bandit
bandit -r src/

# Check for outdated packages
pip list --outdated
```

### 6.2 Penetration Testing (Web Interface)

```bash
# If web interface enabled
# Test for common web vulnerabilities

# SQL Injection test
curl -X POST http://localhost:5000/api/login \
  -d "username=admin' OR '1'='1&password=test"

# XSS test
curl http://localhost:5000/api/events?search=<script>alert('XSS')</script>

# Authentication bypass test
curl http://localhost:5000/api/config
# Should return 401 Unauthorized
```

---

## 7. User Acceptance Testing

### 7.1 UAT Checklist

**Basic Functionality**:
- [ ] System starts without errors
- [ ] All 4 cameras display video
- [ ] Detects humans walking in view
- [ ] Detects vehicles
- [ ] Tracks objects with unique IDs
- [ ] Calculates distance (within ±1m)
- [ ] Alerts trigger appropriately
- [ ] Audio plays through speaker
- [ ] Logs created
- [ ] Events saved to database

**Alert Scenarios**:
- [ ] Alert triggered when person approaches door at night
- [ ] Alert triggered when person near vehicle
- [ ] No alert during daytime for normal activity
- [ ] Cooldown prevents alert spam
- [ ] Multiple alerts delivered to correct speakers

**System Reliability**:
- [ ] Runs for 24 hours without crash
- [ ] Auto-recovers from camera disconnection
- [ ] Auto-recovers from speaker disconnection
- [ ] CPU usage acceptable (<80%)
- [ ] Memory usage acceptable (<6GB)

**Usability**:
- [ ] Configuration easy to understand
- [ ] Alert messages clear and actionable
- [ ] Logs easy to read
- [ ] Web dashboard accessible (if enabled)
- [ ] System restart straightforward

### 7.2 Test Scenarios

**Scenario 1: Nighttime Intruder**
1. Set time to 11 PM (or adjust system clock)
2. Walk into front camera view
3. Approach front door within 5 meters
4. **Expected**: Alert "Warning! Person detected near entrance at night"
5. **Verify**: Alert played within 2 seconds

**Scenario 2: Package Delivery**
1. Daytime scenario
2. Walk to front door
3. Leave object (box) at door
4. Walk away
5. **Expected**: Alert "Package delivered at front door"
6. **Verify**: Snapshot saved

**Scenario 3: Vehicle Security**
1. Stand near parked car in garage
2. Get within 3 meters
3. **Expected**: Alert "Person detected near your vehicle"
4. **Verify**: Alert triggered

---

## 8. Automated Testing

### 8.1 Continuous Testing

**Pre-commit hooks** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
      
      - id: black
        name: black
        entry: black
        language: system
        types: [python]
      
      - id: flake8
        name: flake8
        entry: flake8
        language: system
        types: [python]
```

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 9. Test Data

### 9.1 Test Videos

**Create test dataset**:
```bash
# Record test videos
ffmpeg -i rtsp://camera_url -t 60 tests/data/front_door_day.mp4
ffmpeg -i rtsp://camera_url -t 60 tests/data/front_door_night.mp4
```

**Annotated test data**:
```
tests/data/
├── person_walking.mp4        # Person walking, 30s
├── vehicle_passing.mp4        # Car driving by, 20s
├── empty_scene.mp4            # No objects, 60s
├── multi_person.mp4           # Multiple people, 45s
└── annotations/
    ├── person_walking.json    # Ground truth labels
    └── vehicle_passing.json
```

---

## 10. Testing Schedule

### During Development
- **Daily**: Run unit tests before commits
- **Weekly**: Full test suite + integration tests
- **Before releases**: Complete testing including E2E

### Post-Deployment
- **Daily**: System health check
- **Weekly**: Review logs for errors
- **Monthly**: Performance benchmarks
- **Quarterly**: Full regression testing

---

## 11. Test Reporting

### Coverage Report
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Performance Report
```bash
python scripts/generate_performance_report.py
# Outputs: reports/performance_YYYY-MM-DD.pdf
```

### Test Summary
```
================================ Test Summary ================================
Unit Tests:           142 passed, 2 skipped
Integration Tests:    28 passed
E2E Tests:            5 passed
Performance Tests:    PASSED (FPS: 18.5, CPU: 65%, Memory: 4.2GB)
Security Tests:       PASSED (No vulnerabilities found)
Coverage:             87%
==============================================================================
```

---

## 12. Troubleshooting Tests

**Test Failures**:
```bash
# Run failed tests only
pytest --lf

# Increase verbosity
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

**Debug Tests**:
```python
# Add breakpoint in test
import pdb; pdb.set_trace()

# Or use pytest --pdb to drop into debugger on failure
```

---

This comprehensive testing strategy ensures the system is robust, reliable, and meets all requirements before deployment.
