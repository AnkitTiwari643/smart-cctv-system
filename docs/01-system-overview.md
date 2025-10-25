# System Overview and Objectives

## 1. Project Vision

Transform a basic 4-camera CCTV system into an intelligent security platform that provides:
- Automated monitoring with minimal human intervention
- Proactive threat detection and alerting
- Detailed situational awareness through object classification and distance measurement
- Immediate response capability through audio alerts

## 2. Primary Goals

### 2.1 Core Functionality
1. **Real-Time Object Detection**
   - Detect objects in video streams with <200ms latency
   - Support for multiple object classes: humans, vehicles, animals, packages
   - Maintain 15+ FPS processing rate per camera

2. **Object Classification and Tracking**
   - Identify object types with >85% accuracy
   - Track objects across frames with unique IDs
   - Maintain tracking through brief occlusions

3. **Distance Measurement**
   - Calculate distance between detected humans and:
     - Entry/exit points (doors, gates)
     - Vehicles (cars, motorcycles)
     - Other critical zones (safe, garage)
   - Accuracy: ±1 meter for distances up to 20 meters

4. **Real-Time Alert System**
   - Trigger alerts based on configurable rules
   - Deliver audio messages via wired or Bluetooth speakers
   - Alert delivery time: <2 seconds from detection

### 2.2 System Characteristics
- **Scalability**: Start with 4 cameras, expand to 8+ cameras
- **Affordability**: Use free, open-source software
- **Accessibility**: Run on existing old laptop hardware
- **Reliability**: 99%+ uptime during monitoring hours
- **Privacy**: All processing local, no cloud dependency

## 3. Success Criteria

### 3.1 Functional Success Metrics
- [ ] Successfully capture and process video from all 4 cameras simultaneously
- [ ] Detect humans with >90% accuracy (measured on test dataset)
- [ ] Detect vehicles with >85% accuracy
- [ ] Calculate distance with ±1m accuracy for objects within 20m
- [ ] Deliver alerts within 2 seconds of detection event
- [ ] System runs continuously for 24+ hours without crashes
- [ ] False positive rate <5% (configurable sensitivity)

### 3.2 Performance Success Metrics
- [ ] Process 4 camera streams at 15+ FPS each on target hardware
- [ ] CPU utilization <80% average during normal operation
- [ ] Memory usage <6GB on 8GB system
- [ ] Alert system responds <500ms to trigger events
- [ ] System boot/restart time <60 seconds

### 3.3 Usability Success Metrics
- [ ] Configuration changes possible without code modification
- [ ] Setup time from fresh install: <2 hours
- [ ] Clear, actionable alerts (no cryptic messages)
- [ ] Web dashboard accessible from local network
- [ ] Logs searchable and understandable

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SMART CCTV SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Camera 1    │  │  Camera 2    │  │  Camera 3    │  │  Camera 4    │
│  (Front)     │  │  (Back)      │  │  (Side)      │  │  (Garage)    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Video Stream Capture │
                    │  (RTSP/HTTP)          │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Frame Preprocessing  │
                    │  (Resize, Normalize)  │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Object Detection     │
                    │  (YOLO v8 / SSD)      │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
    ┌───────────▼────────┐  ┌──▼──────────┐  ┌▼──────────────┐
    │ Object Tracking    │  │ Classification│  │Distance Calc  │
    │ (DeepSORT)         │  │ (Human/Vehicle│  │(Monocular/    │
    └───────────┬────────┘  │ /Animal/Other)│  │Calibrated)    │
                │           └──┬──────────┘  └┬──────────────┘
                │              │              │
                └──────────────┴──────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Alert Rule Engine    │
                    │  (Evaluate Conditions)│
                    └───────────┬───────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
    ┌───────────▼────────┐  ┌──▼──────────┐  ┌▼──────────────┐
    │ Audio Alert System │  │  Logging    │  │  Web Dashboard│
    │ (Wired/Bluetooth   │  │  System     │  │  (Optional)   │
    │  Speaker)          │  │             │  │               │
    └────────────────────┘  └─────────────┘  └───────────────┘
```

## 5. System Components Overview

### 5.1 Input Layer
- **Video Capture Module**: Connects to IP cameras via RTSP/HTTP
- **Audio Capture Module**: Records audio from camera microphones (future)
- **Configuration Loader**: Reads system settings from YAML files

### 5.2 Processing Layer
- **Preprocessing Pipeline**: Frame resizing, normalization, buffering
- **Object Detection Engine**: Deep learning model inference
- **Object Tracker**: Multi-object tracking with unique IDs
- **Distance Calculator**: Monocular depth estimation or calibration-based
- **Classification Engine**: Categorizes detected objects

### 5.3 Logic Layer
- **Alert Rule Engine**: Evaluates conditions and triggers alerts
- **Event Manager**: Handles detection events and state management
- **Data Logger**: Records events, detections, and system metrics

### 5.4 Output Layer
- **Alert Delivery System**: Sends audio messages to speakers
- **Notification System**: Email/SMS notifications (optional)
- **Web Dashboard**: Real-time monitoring interface (optional)
- **Data Storage**: Saves events and snapshots

## 6. Use Cases

### 6.1 Primary Use Cases

**UC1: Intruder Detection at Night**
- **Actor**: Homeowner (sleeping)
- **Trigger**: Human detected in backyard after 10 PM
- **Flow**:
  1. Camera 2 (back) detects human figure
  2. System classifies object as "human"
  3. Calculates distance: 5 meters from back door
  4. Evaluates rule: "Human detected at night within 10m of entrance"
  5. Triggers alert: "Warning: Person detected near back door"
  6. Plays audio message through bedroom speaker
  7. Logs event with snapshot
- **Success**: Homeowner awakened and aware within 2 seconds

**UC2: Package Delivery Monitoring**
- **Actor**: Homeowner (at work)
- **Trigger**: Human approaches front door, then leaves
- **Flow**:
  1. Camera 1 (front) detects human
  2. Tracks human movement to door
  3. Human leaves, new object detected (package)
  4. System logs "delivery event"
  5. Optional: Sends notification to phone
- **Success**: Homeowner knows package arrived safely

**UC3: Vehicle Proximity Alert**
- **Actor**: Homeowner (in house)
- **Trigger**: Human detected within 3 meters of parked car
- **Flow**:
  1. Camera 4 (garage) detects human
  2. Calculates distance to vehicle: 2.5 meters
  3. Evaluates rule: "Human within 3m of vehicle"
  4. Triggers alert: "Person near your vehicle"
  5. Plays message through living room speaker
- **Success**: Homeowner checks situation immediately

### 6.2 Secondary Use Cases
- **UC4**: Animal detection (raccoon, stray dog) - low-priority alert
- **UC5**: Vehicle traffic monitoring and counting
- **UC6**: Loitering detection (person stationary for 5+ minutes)
- **UC7**: Historical event search and playback

## 7. Non-Functional Requirements

### 7.1 Performance
- Real-time processing: <200ms latency per frame
- Concurrent camera handling: 4 cameras minimum
- Scalability: Support up to 8 cameras with hardware upgrade
- Resource efficiency: Run on 8GB RAM, older CPU

### 7.2 Reliability
- Uptime: 99%+ during monitoring hours
- Auto-recovery: Restart failed camera connections
- Graceful degradation: Continue with remaining cameras if one fails
- Data persistence: No loss of alert history on restart

### 7.3 Security
- Local processing: No data sent to cloud
- Encrypted storage: Sensitive configuration encrypted
- Access control: Password-protected web interface
- Network isolation: System on isolated VLAN (recommended)

### 7.4 Usability
- Configuration: YAML files, no code changes needed
- Installation: Single script for dependency setup
- Monitoring: Web dashboard for live view
- Maintenance: Automatic log rotation, disk space management

### 7.5 Maintainability
- Modular design: Components independently replaceable
- Logging: Comprehensive logs for troubleshooting
- Documentation: Inline code comments, external guides
- Updates: Easy model updates without system redesign

## 8. Constraints and Assumptions

### 8.1 Constraints
- **Budget**: $0 for software (open-source only)
- **Hardware**: Must run on existing old laptop
- **Network**: Cameras must be on same LAN as laptop
- **Power**: System must handle brief power outages gracefully
- **Storage**: Limited to laptop disk space (manage retention)

### 8.2 Assumptions
- Cameras support RTSP or HTTP streaming protocols
- Cameras have fixed mounting positions
- Network bandwidth sufficient for 4x 1080p streams
- Laptop remains powered on and connected
- User has basic command-line familiarity
- Home has WiFi or wired network for laptop
- Speakers have 3.5mm jack or Bluetooth support

## 9. Future Expansion Possibilities

### 9.1 Phase 2 Features (6-12 months)
- Facial recognition for known persons vs. strangers
- License plate recognition (ALPR)
- Audio analysis (breaking glass, shouting)
- Mobile app for remote monitoring
- Cloud backup of critical events

### 9.2 Phase 3 Features (12+ months)
- AI-powered behavior analysis (suspicious activity)
- Integration with smart home systems (lights, locks)
- Advanced analytics dashboard with trends
- Multi-site support (monitor multiple properties)
- Edge TPU acceleration for improved performance

## 10. Out of Scope

The following are explicitly **not** included in the initial version:
- ❌ Cloud video storage
- ❌ Facial recognition
- ❌ License plate recognition
- ❌ Mobile application
- ❌ Smart home integration
- ❌ Multi-user access control
- ❌ Video recording (only snapshots)
- ❌ Audio processing/analysis
- ❌ Motion-triggered recording
- ❌ PTZ camera control

These may be added in future versions but are not part of the MVP.
