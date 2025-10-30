# Docker Deployment Guide - Smart CCTV System

## 🐳 Docker Services Overview

The Smart CCTV System now provides multiple Docker deployment options:

### Main Services

1. **`smart-cctv`** - Complete system (CCTV detection + Web interface)
2. **`smart-cctv-web`** - Web interface only (profile: `web-only`)
3. **`smart-cctv-demo`** - Demo with sample data (profile: `demo`)

### Utility Services

4. **`model-downloader`** - Downloads YOLO models (profile: `tools`)
5. **`database-manager`** - Database initialization (profile: `tools`)

## 🚀 Quick Start

### 1. Complete System (Recommended)
```bash
# Copy environment configuration
cp .env.example .env

# Edit .env file with your settings
nano .env

# Start complete system
docker-compose up -d smart-cctv

# Access web interface
open http://localhost:5000
```

### 2. Demo Mode
```bash
# Start demo with sample data
docker-compose --profile demo up -d smart-cctv-demo

# Access demo
open http://localhost:5000
```

### 3. Web Interface Only
```bash
# Start only web interface (requires existing CCTV system)
docker-compose --profile web-only up -d smart-cctv-web

# Access interface
open http://localhost:5000
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

**Critical settings to change:**
```env
# Security (CHANGE THESE!)
WEB_INTERFACE_SECRET_KEY=your-unique-secret-key
WEB_INTERFACE_USERNAME=your-username
WEB_INTERFACE_PASSWORD=your-secure-password

# Camera credentials
CAMERA_1_PASSWORD=your-camera-password
CAMERA_2_PASSWORD=your-camera-password
```

### Volume Mounts

- `./config:/app/config` - Configuration files
- `./data:/app/data` - Recordings, snapshots, logs
- `./models:/app/models` - AI models
- `sqlite_data:/app/data` - Persistent database

### Network Configuration

- **Port 5000**: Web interface
- **Port 8080**: Additional service port
- **Network**: `smart-cctv-network` (bridge)

## 📊 Service Deployment Options

### Option 1: All-in-One (Default)
```bash
docker-compose up -d
```
Runs complete CCTV system with web interface.

### Option 2: Microservices
```bash
# Start main CCTV detection
docker-compose up -d smart-cctv

# Start separate web interface
docker-compose --profile web-only up -d smart-cctv-web
```

### Option 3: Development/Demo
```bash
# Demo mode with sample data
docker-compose --profile demo up -d smart-cctv-demo
```

## 🛠️ Management Commands

### Database Management
```bash
# Initialize database
docker-compose --profile tools run --rm database-manager

# Backup database
docker-compose exec smart-cctv cp /app/data/alerts.db /app/data/backup_alerts.db

# View database
docker-compose exec smart-cctv sqlite3 /app/data/alerts.db
```

### Model Management
```bash
# Download models
docker-compose --profile tools run --rm model-downloader

# Update models
docker-compose exec smart-cctv python scripts/download_models.py
```

### Service Management
```bash
# View logs
docker-compose logs -f smart-cctv

# Restart services
docker-compose restart smart-cctv

# Update and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔍 Monitoring & Debugging

### Health Checks
```bash
# Check service health
docker-compose ps

# Manual health check
curl http://localhost:5000/health
```

### Log Monitoring
```bash
# Real-time logs
docker-compose logs -f smart-cctv

# Web interface logs only
docker-compose logs -f smart-cctv | grep -i "web\|flask\|http"

# Error logs only
docker-compose logs smart-cctv | grep -i "error\|exception\|failed"
```

### Resource Monitoring
```bash
# Container resource usage
docker stats smart-cctv-system

# Disk usage
docker system df

# Volume inspection
docker volume inspect smart-cctv-database
```

## 🔒 Security Considerations

### Production Deployment
```bash
# Use production environment
echo "FLASK_ENV=production" >> .env

# Restrict network access
# Edit docker-compose.yml to bind to localhost only:
# ports:
#   - "127.0.0.1:5000:5000"
```

### SSL/HTTPS Setup
Add reverse proxy (nginx) for HTTPS:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/ssl/certs
  depends_on:
    - smart-cctv
```

## 🎯 Deployment Profiles

### Profile: `demo`
```bash
docker-compose --profile demo up -d
```
- Sample data and alerts
- Development environment
- Demo credentials (admin/admin123)

### Profile: `web-only`
```bash
docker-compose --profile web-only up -d
```
- Web interface without CCTV detection
- Requires external CCTV system
- Read-only data access

### Profile: `tools`
```bash
docker-compose --profile tools run --rm model-downloader
docker-compose --profile tools run --rm database-manager
```
- Utility services
- One-time operations
- Database and model management

## 🔄 Updates and Maintenance

### Update System
```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify update
curl http://localhost:5000/health
```

### Backup Data
```bash
# Create backup
docker-compose exec smart-cctv tar czf /app/data/backup-$(date +%Y%m%d).tar.gz /app/data

# Copy backup to host
docker cp smart-cctv-system:/app/data/backup-$(date +%Y%m%d).tar.gz ./
```

### Clean Up
```bash
# Remove unused containers and images
docker system prune -f

# Remove specific volumes (WARNING: deletes data)
docker volume rm smart-cctv-database

# Reset demo data
docker volume rm smart-cctv-demo-data
```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Find process using port
   lsof -i :5000
   
   # Change port in docker-compose.yml
   ports:
     - "5001:5000"  # Use different host port
   ```

2. **Permission errors:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER ./data ./config
   chmod -R 755 ./data ./config
   ```

3. **Database locked:**
   ```bash
   # Stop all containers
   docker-compose down
   
   # Remove database lock
   docker-compose exec smart-cctv rm -f /app/data/alerts.db-journal
   
   # Restart
   docker-compose up -d
   ```

4. **Memory issues:**
   ```bash
   # Add memory limits to docker-compose.yml
   mem_limit: 2g
   memswap_limit: 2g
   ```

### Debug Mode
```bash
# Enable debug mode
echo "FLASK_ENV=development" >> .env
docker-compose restart smart-cctv

# View detailed logs
docker-compose logs -f smart-cctv
```

## 📁 File Structure
```
smart-cctv-system/
├── docker-compose.yml      # Main orchestration
├── Dockerfile             # Container definition
├── .env.example           # Environment template
├── config/               # Configuration files
├── data/                # Persistent data
│   ├── logs/           # Application logs
│   ├── snapshots/      # Camera snapshots
│   └── alerts.db       # SQLite database
├── models/              # AI models
└── src/                # Application source
```

---

**🎯 Ready for professional deployment!**

The Docker setup provides enterprise-grade containerization with multiple deployment options, comprehensive monitoring, and production-ready security features.