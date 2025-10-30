# Smart CCTV System - Web Interface Guide

## 🌟 Overview

The Smart CCTV System now includes a comprehensive web-based management interface that provides:

- **Real-time Dashboard** - Monitor system status, alerts, and performance
- **Configuration Management** - Easy-to-use interface for all system settings
- **Alert Management** - View, filter, and manage security alerts
- **Camera Feeds** - Live camera monitoring and control
- **System Monitoring** - Performance metrics and health monitoring
- **Mobile-Responsive Design** - Works perfectly on phones, tablets, and desktops

## 🚀 Quick Start

### Option 1: Web Interface Only (for initial setup)
```bash
python run_web.py
```

### Option 2: Complete System (CCTV + Web Interface)
```bash
python start_system.py
```

### Option 3: Using Docker
```bash
docker-compose up
```

## 🌐 Accessing the Interface

1. **Start the web interface** using one of the methods above
2. **Open your browser** and go to: http://localhost:5000
3. **Login** with default credentials:
   - Username: `admin`
   - Password: `admin123`

## 📱 Interface Features

### 1. Dashboard
- **System Overview**: Real-time status indicators
- **Alert Summary**: Recent alerts and trends
- **Camera Status**: Live feed status for all cameras
- **Performance Metrics**: CPU, memory, and system health
- **Quick Actions**: Common tasks and shortcuts

### 2. Configuration Management
The configuration page provides tabbed interface for:

#### Camera Settings
- Add/remove cameras
- Configure camera URLs and settings
- Set detection zones
- Adjust quality and FPS settings

#### Detection Settings  
- Object detection parameters
- Confidence thresholds
- Tracking settings
- Performance optimization

#### Alert Rules
- Motion detection rules
- Object-specific alerts
- Time-based rules
- Notification settings

#### Audio & TTS
- Text-to-speech configuration
- Audio alert settings
- Voice selection (now using gTTS)
- Volume and timing controls

#### UI Preferences
- Interface theme settings
- Notification preferences
- Dashboard layout options
- Mobile responsiveness settings

### 3. Alert Management
- **Real-time alerts**: Live feed of security events
- **Filtering**: By type, camera, time, severity
- **Bulk operations**: Acknowledge multiple alerts
- **Export**: Download alert reports
- **Alert details**: View snapshots and metadata

### 4. Camera Monitoring
- **Live feeds**: Real-time video streams
- **Camera controls**: Play/pause, fullscreen, snapshots
- **Grid/list views**: Flexible layout options
- **Camera settings**: Per-camera configuration
- **Status monitoring**: Online/offline detection

### 5. System Monitor
- **Performance charts**: Real-time CPU, memory, disk usage
- **Temperature monitoring**: System thermal status
- **Process monitoring**: Running services and their resource usage
- **Network activity**: Upload/download statistics
- **System logs**: Real-time log viewing and export

## 🔧 Configuration

### Web Interface Settings

Add this section to your `config.yaml`:

```yaml
# Web interface configuration
web_interface:
  host: "0.0.0.0"        # Listen on all interfaces
  port: 5000             # Web server port
  debug: false           # Enable debug mode (development only)
  secret_key: "your-secret-key-here"  # Change this!
  
  # Authentication
  auth:
    username: "admin"
    password: "admin123"   # Change this!
    session_timeout: 3600  # 1 hour
  
  # Database
  database:
    path: "data/alerts.db"
  
  # Real-time updates
  socketio:
    cors_allowed_origins: "*"
    ping_timeout: 60
    ping_interval: 25
```

### Security Settings

**⚠️ Important**: Change default credentials!

1. Edit `config.yaml` and update:
   ```yaml
   web_interface:
     auth:
       username: "your-username"
       password: "your-secure-password"
     secret_key: "your-unique-secret-key"
   ```

2. For production deployment:
   ```yaml
   web_interface:
     host: "127.0.0.1"  # Restrict to localhost
     debug: false       # Never enable in production
   ```

## 🎨 Interface Themes

The web interface features a modern dark theme with:
- **Bootstrap 5** for responsive design
- **Custom dark color scheme** optimized for security monitoring
- **Mobile-first design** that works on all devices
- **Real-time updates** using WebSocket connections
- **Interactive charts** with Chart.js
- **Professional iconography** with Bootstrap Icons

## 🔄 Real-time Features

The interface provides real-time updates for:
- **System metrics**: CPU, memory, temperature
- **Alert notifications**: New alerts appear instantly
- **Camera status**: Online/offline changes
- **Log entries**: Live system logs
- **Performance charts**: Auto-updating graphs

## 📊 Data Export

Export capabilities include:
- **Alert reports**: CSV/JSON format
- **System reports**: Comprehensive system status
- **Log files**: Complete system logs
- **Configuration backup**: YAML format

## 🐳 Docker Deployment

For containerized deployment:

```dockerfile
# Dockerfile already includes web interface
FROM python:3.9-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Expose web interface port
EXPOSE 5000

# Start complete system
CMD ["python", "start_system.py"]
```

## 🔧 Development

### Adding New Features

1. **Backend**: Extend `src/web_interface.py`
2. **Frontend**: Add new templates in `src/templates/`
3. **API**: Add new routes for data endpoints
4. **Real-time**: Use SocketIO for live updates

### Template Structure

```
src/templates/
├── base.html          # Main layout with navigation
├── dashboard.html     # System dashboard
├── config.html        # Configuration management
├── alerts.html        # Alert management
├── cameras.html       # Camera monitoring
├── system.html        # System monitoring
└── login.html         # Authentication
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Change port in config.yaml or use:
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Database errors**:
   ```bash
   # Remove database and restart:
   rm data/alerts.db
   python run_web.py
   ```

3. **Configuration not loading**:
   ```bash
   # Check config file exists:
   ls config/config.yaml
   
   # Copy from example if needed:
   cp config/config.example.yaml config/config.yaml
   ```

4. **Permission errors**:
   ```bash
   # Make scripts executable:
   chmod +x run_web.py start_system.py
   ```

### Debug Mode

Enable debug mode for development:
```yaml
web_interface:
  debug: true
```

This provides:
- Detailed error messages
- Auto-reload on code changes
- Debug toolbar
- Verbose logging

## 📝 API Endpoints

The web interface provides REST API endpoints:

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/alerts` - Get alerts (with filtering)
- `POST /api/alerts/<id>/acknowledge` - Acknowledge alert
- `GET /api/system/stats` - Get system statistics
- `GET /api/cameras/status` - Get camera status

## 🌍 Mobile Access

Access the interface from mobile devices:
1. **Connect to same network** as the CCTV system
2. **Find system IP address**: `hostname -I` (Linux) or `ipconfig` (Windows)
3. **Access via mobile browser**: `http://[IP-ADDRESS]:5000`

## 🔐 Security Considerations

- Change default credentials immediately
- Use HTTPS in production (add SSL proxy)
- Restrict network access (firewall rules)
- Regular security updates
- Monitor access logs
- Use strong session secrets

## 📚 Additional Resources

- [Installation Guide](INSTALL.md)
- [Configuration Reference](docs/04-installation-guide.md)
- [Alert System Documentation](docs/05-alert-system.md)
- [API Documentation](docs/api.md)

---

**🎯 Ready to monitor your security system with style!**

The web interface transforms your Smart CCTV system into a professional security monitoring solution with enterprise-grade features and consumer-friendly usability.