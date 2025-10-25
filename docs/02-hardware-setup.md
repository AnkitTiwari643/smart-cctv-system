# Hardware Setup Guide

## 1. Existing CCTV System

### 1.1 Camera Specifications

#### Minimum Camera Requirements
- **Type**: IP Network Camera (not analog CCTV)
- **Protocol**: RTSP, RTMP, or HTTP/MJPEG streaming support
- **Resolution**: 720p (1280x720) minimum, 1080p (1920x1080) recommended
- **Frame Rate**: 15 FPS minimum, 25-30 FPS recommended
- **Features**: 
  - Built-in microphone (for audio alerts)
  - Night vision (IR LEDs)
  - Fixed lens (PTZ adds complexity)
- **Network**: Ethernet (PoE preferred) or WiFi
- **Power**: PoE, 12V DC, or USB power

#### Typical Compatible Cameras
- Hikvision DS-2CD2xxx series
- Dahua IPC-HDW/HFW series
- Reolink RLC-xxx series
- TP-Link Tapo C200/C310
- Amcrest IP2M/IP3M series
- Generic ONVIF-compatible cameras

#### Camera Placement (4-Camera Setup)
```
┌─────────────────────────────────────┐
│              HOUSE                  │
│                                     │
│  [Cam4]                    [Cam3]   │
│  Garage      Living       Side      │
│              Room         Entrance  │
│                                     │
│      ┌──────────┐                   │
│      │   Door   │                   │
└──────┴──────────┴──────────────────┘
         [Cam1]              [Cam2]
         Front Door          Backyard
```

**Camera 1 - Front Door/Entrance**
- Coverage: Main entrance, driveway approach
- Height: 2.5-3m (8-10 feet)
- Angle: 30° downward, covering 5-10m range
- Priority: HIGHEST (primary entry point)

**Camera 2 - Backyard/Rear**
- Coverage: Back door, yard, fence line
- Height: 2.5-3m
- Angle: 30° downward, covering 10-15m
- Priority: HIGH (secondary entry point)

**Camera 3 - Side Entrance/Gate**
- Coverage: Side door, pathway, gate
- Height: 2.5-3m
- Angle: Narrow field covering 3-8m
- Priority: MEDIUM

**Camera 4 - Garage/Driveway**
- Coverage: Vehicle parking area, garage door
- Height: 2.5-3m
- Angle: Wide field covering parked vehicles
- Priority: MEDIUM (asset protection)

### 1.2 Camera Network Configuration

#### Option A: Wired Ethernet (Recommended)
```
[Router/Switch] ─── [PoE Switch] ─┬─── [Camera 1]
       │                           ├─── [Camera 2]
       │                           ├─── [Camera 3]
       │                           └─── [Camera 4]
       │
       └─── [Laptop/Server]
```

**Advantages**:
- Reliable connection
- Higher bandwidth
- PoE provides power and data
- Lower latency

**Requirements**:
- PoE switch (4+ ports) or PoE injectors
- Cat5e/Cat6 ethernet cables
- Network configuration access

#### Option B: WiFi
```
[WiFi Router] ─┬─── [Camera 1] (WiFi)
               ├─── [Camera 2] (WiFi)
               ├─── [Camera 3] (WiFi)
               ├─── [Camera 4] (WiFi)
               └─── [Laptop] (WiFi/Wired)
```

**Advantages**:
- Easier installation
- No cable running needed

**Disadvantages**:
- Less reliable
- Potential interference
- Higher latency
- Bandwidth limitations with 4 cameras

**Requirements**:
- Strong WiFi signal at all camera locations
- WiFi router with 802.11n or better
- 2.4GHz or 5GHz band
- QoS settings to prioritize camera traffic

#### Network Settings
- **IP Addressing**: Static IPs for all cameras (e.g., 192.168.1.101-104)
- **Subnet**: Same subnet as laptop (e.g., 192.168.1.0/24)
- **VLAN** (optional): Isolated VLAN for cameras (security)
- **Bandwidth**: ~4-8 Mbps per 1080p camera = 32 Mbps total

### 1.3 Getting Camera Stream URLs

Each camera manufacturer has different URL formats:

**Generic RTSP Format**:
```
rtsp://username:password@192.168.1.101:554/stream1
```

**Common Formats by Brand**:
- **Hikvision**: `rtsp://admin:password@192.168.1.101:554/Streaming/Channels/101`
- **Dahua**: `rtsp://admin:password@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0`
- **Reolink**: `rtsp://admin:password@192.168.1.101:554/h264Preview_01_main`
- **Amcrest**: `rtsp://admin:password@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0`
- **TP-Link Tapo**: Use ONVIF protocol or HTTP

**Testing Camera Streams**:
```bash
# Using VLC Media Player
vlc rtsp://admin:password@192.168.1.101:554/stream1

# Using ffplay (from FFmpeg)
ffplay rtsp://admin:password@192.168.1.101:554/stream1

# Using OpenCV (Python)
python -c "import cv2; cap=cv2.VideoCapture('rtsp://admin:password@192.168.1.101:554/stream1'); print('Connected' if cap.isOpened() else 'Failed')"
```

## 2. Laptop/Server Specifications

### 2.1 Minimum Requirements (Old Laptop)

**CPU**:
- Intel Core i5 (4th gen or newer) - 4 cores
- AMD Ryzen 3 or equivalent
- Passmark score: 4000+
- 64-bit processor required

**RAM**:
- Minimum: 8GB DDR3/DDR4
- Recommended: 12GB or 16GB
- Swap space: 4GB (if only 8GB RAM)

**Storage**:
- Minimum: 100GB free space
- Recommended: 256GB SSD or 500GB HDD
- SSD strongly recommended for better performance
- Retention: ~30 days of event snapshots

**GPU** (Optional but helpful):
- NVIDIA GPU with CUDA support (GTX 950 or better)
- Intel HD Graphics 4000+ for Intel Quick Sync
- AMD GPU with ROCm support
- Note: CPU-only is viable with optimized models

**Network**:
- Gigabit Ethernet (1000 Mbps) preferred
- WiFi 802.11ac if using wireless
- Minimum: 100 Mbps for 4 cameras

**Operating System**:
- **Ubuntu 20.04/22.04 LTS** (recommended)
- Debian 11+
- Windows 10/11 Pro (works but more overhead)
- macOS 10.15+ (works but limited testing)

**Ports**:
- USB 2.0/3.0 ports (for Bluetooth dongle if needed)
- 3.5mm audio jack (for wired speaker)
- Ethernet port (RJ45)

### 2.2 Recommended Specifications (Better Performance)

**CPU**: Intel Core i7 (6th gen+) or Ryzen 5
**RAM**: 16GB
**Storage**: 256GB NVMe SSD
**GPU**: NVIDIA GTX 1050 Ti or better (enables faster processing)

### 2.3 Performance Estimates

| Hardware Config | Cameras | FPS/Cam | CPU Usage | Latency |
|----------------|---------|---------|-----------|---------|
| Min (i5 4th, 8GB, No GPU) | 4 | 10-15 | 70-85% | 150-200ms |
| Min + GPU (GTX 950) | 4 | 15-20 | 40-60% | 100-150ms |
| Recommended (i7 6th, 16GB, GTX 1050Ti) | 4 | 25-30 | 30-50% | 50-100ms |
| High-end (i7 10th, 32GB, RTX 3060) | 8 | 30 | 20-40% | 30-50ms |

### 2.4 Laptop Setup Checklist

- [ ] Disable sleep mode / suspend
- [ ] Set performance power plan (not power saver)
- [ ] Disable screen timeout
- [ ] Enable SSH for remote access (Linux/Mac)
- [ ] Configure static IP or reserve DHCP
- [ ] Install OS updates
- [ ] Configure firewall rules
- [ ] Set up automatic login (optional, for auto-start)
- [ ] Install remote desktop software (optional)

## 3. Speaker System

### 3.1 Wired Speaker (Recommended)

**Type**: Active/Powered speaker with 3.5mm input

**Specifications**:
- Input: 3.5mm (1/8") audio jack
- Power: AC powered (not battery for 24/7)
- Output: 5W+ RMS
- Features: Volume control accessible

**Recommended Models**:
- Logitech Z200/Z313 (2.1 speakers)
- Creative Pebble V2/V3
- AmazonBasics USB-powered speakers
- Any computer speakers with 3.5mm jack

**Placement**:
- Central location (living room, bedroom)
- Near where you spend most time
- Multiple speakers in different rooms (optional)

**Setup**:
```
[Laptop] ──(3.5mm cable)──> [Powered Speaker]
```

**Advantages**:
- Reliable, no pairing needed
- Low latency (instant)
- No battery concerns
- Cheaper

**Disadvantages**:
- Cable length limitation (3-5m typically)
- Less flexible placement

**Cost**: $10-50

### 3.2 Bluetooth Speaker

**Type**: Bluetooth speaker with auto-connect

**Specifications**:
- Bluetooth: 4.0 or higher
- Range: 10m+ (Class 2)
- Battery: 8+ hours (or AC powered)
- Auto-reconnect: Yes (critical)

**Recommended Models**:
- JBL Flip 5/6
- Anker Soundcore 2
- Amazon Echo Dot (can also use Alexa TTS)
- UE Boom 3

**Bluetooth Adapter** (if laptop lacks Bluetooth):
- USB Bluetooth 4.0+ dongle
- Compatible with Linux (check driver support)
- Examples: TP-Link UB400, ASUS USB-BT400

**Setup**:
```
[Laptop] ~~~(Bluetooth)~~~> [Bluetooth Speaker]
         [USB BT Dongle]
```

**Advantages**:
- Wireless, flexible placement
- Modern, sleek
- Can be portable

**Disadvantages**:
- Connection drops possible
- Higher latency (500ms-1s)
- Battery management needed
- Pairing complexity
- Slightly more expensive

**Cost**: $30-100

### 3.3 Hybrid Setup (Best)

Use both for redundancy:
- **Primary**: Wired speaker in bedroom (night alerts)
- **Secondary**: Bluetooth speaker in living room (day alerts)

System can be configured to use both simultaneously or based on time of day.

## 4. Additional Hardware (Optional)

### 4.1 For Improved Distance Measurement

**Option A: Stereo Camera Setup**
- Add second camera at each location
- Mount 6-10cm apart (baseline)
- Synchronized capture
- Provides depth map
- Cost: $100-200 (4 additional cameras)

**Option B: LiDAR Sensor**
- RP-LiDAR A1/A2
- TF-Luna/TF-mini Plus
- Provides accurate distance
- Integrate via USB/UART
- Cost: $100-300

**Option C: Ultrasonic Sensors**
- HC-SR04 modules
- Range: 2-400cm
- Arduino/Raspberry Pi interface
- Cost: $5-10 per sensor

**Note**: Initial version uses **monocular depth estimation** (camera calibration-based), so these are optional enhancements.

### 4.2 For Improved Performance

**Coral Edge TPU USB Accelerator**
- Google Coral USB accelerator
- Speeds up TensorFlow Lite models
- 4 TOPS (Trillion operations per second)
- Reduces CPU load significantly
- Cost: $60-75
- Installation: USB 3.0 port

**Intel Neural Compute Stick 2**
- Intel NCS2 (Movidius VPU)
- Accelerates OpenVINO models
- 8 TOPS performance
- USB 3.0 interface
- Cost: $70-100

### 4.3 For Better Reliability

**Uninterruptible Power Supply (UPS)**
- Capacity: 600VA+ (360W+)
- Runtime: 10-30 minutes
- Protects against power outages
- Gives time for graceful shutdown
- Cost: $60-120
- Examples: APC Back-UPS 600VA, CyberPower CP685AVR

**Network UPS** (Optional):
- Separate small UPS for router/switch
- Ensures network stays up during brief outages
- Cost: $40-60

### 4.4 For Expanded Storage

**External Drive**:
- USB 3.0 external HDD/SSD
- Capacity: 1TB+
- For event recordings and snapshots
- Automatic backup location
- Cost: $40-80

**NAS** (Network Attached Storage):
- For centralized storage
- Synology, QNAP, or DIY (Raspberry Pi)
- Stores event history and snapshots
- Cost: $200-500+

## 5. Network Infrastructure

### 5.1 Router Requirements

**Minimum**:
- 4+ Ethernet ports (or use separate switch)
- WiFi 802.11n (if using wireless cameras)
- Support for static IP assignment
- Basic QoS (Quality of Service)

**Recommended**:
- Dual-band router (2.4GHz + 5GHz)
- Gigabit Ethernet ports
- Advanced QoS settings
- VLAN support (for camera isolation)
- VPN server (for remote access)

### 5.2 Network Switch (If Needed)

If router doesn't have enough ports:

**PoE Switch** (Recommended):
- 5-8 port managed or unmanaged
- PoE+ (802.3at) support
- Gigabit ports
- Cost: $60-150
- Examples: TP-Link TL-SG1005P, Netgear GS305P

**Regular Switch**:
- If cameras have separate power
- 5-8 port gigabit
- Cost: $15-40

### 5.3 Cabling

**Ethernet Cables**:
- Cat5e or Cat6
- Lengths as needed (typically 15m-50m)
- Outdoor-rated if running outside
- Pre-made or crimp your own

**Power Cables** (if not using PoE):
- 12V DC extension cables
- Weatherproof connectors
- Appropriate gauge for length

## 6. Hardware Setup Steps

### 6.1 Camera Installation

1. **Physical Mounting**
   - Use camera mounting brackets
   - Secure to wall/soffit/overhang
   - Aim at coverage area
   - Weatherproof all connections

2. **Power Connection**
   - Connect PoE or power adapter
   - Test power LED

3. **Network Connection**
   - Connect Ethernet or configure WiFi
   - Verify network connectivity

4. **Camera Configuration**
   - Access web interface (usually http://192.168.1.xxx)
   - Set static IP address
   - Configure resolution (1080p)
   - Set frame rate (25-30 FPS)
   - Enable RTSP/HTTP stream
   - Set credentials (strong password)
   - Adjust image settings (brightness, contrast)

### 6.2 Laptop Setup

1. **Hardware Preparation**
   - Clean install OS (recommended)
   - Connect to network (wired preferred)
   - Disable sleep/suspend
   - Set static IP or DHCP reservation

2. **Speaker Connection**
   - **Wired**: Plug into 3.5mm jack, test audio
   - **Bluetooth**: Pair device, test connection

3. **Storage Setup**
   - Check free space (100GB minimum)
   - Create data directories
   - Set up automatic cleanup (optional)

### 6.3 Network Verification

Test all cameras are reachable:

```bash
# Ping cameras
ping 192.168.1.101
ping 192.168.1.102
ping 192.168.1.103
ping 192.168.1.104

# Test RTSP stream
ffplay rtsp://admin:password@192.168.1.101:554/stream1
```

## 7. Camera Calibration for Distance Measurement

### 7.1 Why Calibration is Needed

Cameras have lens distortion and unique intrinsic parameters. Calibration allows:
- Accurate distance estimation
- Correction of lens distortion
- 3D position calculation from 2D images

### 7.2 Calibration Process

**Materials Needed**:
- Chessboard pattern (8x6 or 9x7 corners)
- Print on A4/Letter paper or display on tablet
- Good lighting

**Steps**:
1. Print/display chessboard pattern
2. Run calibration script (provided in codebase)
3. Hold pattern at various positions/angles in camera view
4. Capture 20-30 images
5. Script calculates intrinsic parameters
6. Save calibration data per camera

**Time**: 10-15 minutes per camera

### 7.3 Distance Reference Points

For accurate distance calculation, measure and record:
- Camera height from ground (e.g., 2.8m)
- Camera tilt angle (e.g., 30° downward)
- Known distances to reference points (e.g., door is 3m from camera)

These will be entered in configuration files.

## 8. Hardware Troubleshooting

### Common Issues:

**Camera Not Connecting**:
- Check network cable/WiFi signal
- Verify IP address and subnet
- Test with VLC or ffplay
- Check firewall rules
- Restart camera

**Low Frame Rate**:
- Check network bandwidth
- Reduce camera resolution
- Check CPU usage on laptop
- Verify camera settings (FPS)

**Speaker Not Working**:
- Check volume levels (laptop and speaker)
- Test with music file
- Verify audio output device selection
- For Bluetooth: Re-pair device

**Laptop Overheating**:
- Clean dust from vents
- Use cooling pad
- Reduce processing load (lower FPS)
- Check thermal paste (if old laptop)

**Poor Detection Accuracy**:
- Improve camera positioning
- Adjust camera image settings
- Better lighting (add IR illuminators)
- Re-calibrate camera

## 9. Hardware Cost Summary

### Minimum Setup (Using Existing Equipment)
| Item | Cost |
|------|------|
| 4x IP Cameras | $0 (existing) |
| Laptop | $0 (existing) |
| Wired Speaker | $15 |
| Ethernet Cables | $20 |
| **Total** | **$35** |

### Recommended Setup
| Item | Cost |
|------|------|
| 4x IP Cameras (if buying new) | $200-400 |
| Laptop (if buying used) | $200-400 |
| PoE Switch | $80 |
| Wired + Bluetooth Speaker | $60 |
| UPS | $80 |
| Ethernet Cables | $30 |
| **Total** | **$650-1050** |

### Premium Setup
| Item | Cost |
|------|------|
| 4x High-end IP Cameras | $600-800 |
| New Laptop/Mini PC | $500-800 |
| Coral Edge TPU | $70 |
| PoE Switch | $120 |
| Multiple Speakers | $100 |
| UPS | $120 |
| NAS Storage | $300 |
| **Total** | **$1810-2310** |

## 10. Hardware Checklist

- [ ] 4x IP cameras installed and powered
- [ ] All cameras configured with static IPs
- [ ] RTSP/HTTP stream URLs confirmed
- [ ] Network connectivity verified (ping test)
- [ ] Laptop prepared and OS installed
- [ ] Laptop connected to network (wired preferred)
- [ ] Speaker(s) connected and tested
- [ ] Audio output confirmed working
- [ ] Camera coverage areas confirmed (walk test)
- [ ] Camera angles adjusted for optimal view
- [ ] Night vision tested (if using IR)
- [ ] Power backup (UPS) installed (optional)
- [ ] Storage space verified (100GB+ free)
- [ ] Remote access configured (SSH/RDP)

**Ready for Software Installation!**
