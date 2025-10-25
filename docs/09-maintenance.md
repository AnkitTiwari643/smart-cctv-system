# Maintenance and Operations Guide

## 1. Daily Operations

### 1.1 System Monitoring

**Check system status**:
```bash
# Check if system is running
ps aux | grep main.py

# Or if using systemd
sudo systemctl status smart-cctv

# Check resource usage
top -p $(pgrep -f main.py)
```

**Review recent logs**:
```bash
# Check for errors
tail -50 data/logs/errors.log

# Check application log
tail -100 data/logs/app.log

# Check recent alerts
tail -20 data/logs/alerts.log
```

**Verify cameras**:
```bash
# Quick camera test
python scripts/test_cameras.py
```

---

## 2. Weekly Maintenance

### 2.1 Log Review

**Analyze logs for patterns**:
```bash
# Count errors by type
grep "ERROR" data/logs/app.log | cut -d'|' -f4 | sort | uniq -c | sort -rn

# Check camera disconnections
grep "reconnect" data/logs/app.log | wc -l

# Review alert frequency
sqlite3 data/events.db "SELECT COUNT(*) FROM alerts WHERE timestamp > $(date -d '7 days ago' +%s)"
```

### 2.2 Database Maintenance

**Check database size**:
```bash
ls -lh data/events.db
```

**Vacuum database** (compact and optimize):
```bash
sqlite3 data/events.db "VACUUM;"
```

**Verify data retention**:
```bash
# Check oldest event
sqlite3 data/events.db "SELECT datetime(timestamp, 'unixepoch') FROM events ORDER BY timestamp LIMIT 1"
```

### 2.3 Disk Space Management

**Check free space**:
```bash
df -h data/
```

**Clean up old snapshots manually**:
```bash
# Delete snapshots older than 7 days
find data/snapshots -type f -mtime +7 -delete
```

**Clean up old logs**:
```bash
# Compress old logs
find data/logs -name "*.log" -mtime +30 -exec gzip {} \;

# Delete very old compressed logs
find data/logs -name "*.gz" -mtime +90 -delete
```

---

## 3. Monthly Maintenance

### 3.1 System Updates

**Update system packages**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade -y

# macOS
brew update
brew upgrade
```

**Update Python packages**:
```bash
# Activate virtual environment
source venv/bin/activate

# Update packages
pip list --outdated
pip install --upgrade <package_name>

# Or update all (carefully)
pip install --upgrade -r requirements.txt
```

**Update camera firmware**:
- Check manufacturer website for updates
- Download firmware
- Apply via camera web interface
- Test camera connectivity after update

### 3.2 Camera Maintenance

**Physical inspection**:
- [ ] Clean camera lenses
- [ ] Check camera mounting (loose screws?)
- [ ] Inspect cables for damage
- [ ] Clear obstructions (spider webs, debris)
- [ ] Check night vision LEDs working

**Camera configuration check**:
- [ ] Verify time sync
- [ ] Check image quality settings
- [ ] Verify motion detection off (we handle it)
- [ ] Confirm firmware version

### 3.3 Performance Review

**Run performance benchmarks**:
```bash
python scripts/benchmark_fps.py
python scripts/monitor_resources.py --duration 300
```

**Review detection accuracy**:
```bash
# Review false positives
sqlite3 data/events.db "SELECT COUNT(*) FROM alerts WHERE message LIKE '%false%'"

# Review alert frequency
python scripts/analyze_alerts.py --days 30
```

### 3.4 Backup System

**Backup configuration**:
```bash
# Create backup directory
mkdir -p ~/backups/smart-cctv-$(date +%Y%m%d)

# Backup configuration files
cp -r config ~/backups/smart-cctv-$(date +%Y%m%d)/

# Backup database
cp data/events.db ~/backups/smart-cctv-$(date +%Y%m%d)/

# Backup calibration data
cp -r config/calibration ~/backups/smart-cctv-$(date +%Y%m%d)/

# Create compressed archive
tar -czf ~/backups/smart-cctv-$(date +%Y%m%d).tar.gz \
  ~/backups/smart-cctv-$(date +%Y%m%d)
```

**Test backup restoration**:
```bash
# Extract backup
tar -xzf ~/backups/smart-cctv-20250101.tar.gz

# Verify files
ls -la smart-cctv-20250101/
```

---

## 4. Quarterly Maintenance

### 4.1 Security Audit

**Review access logs**:
```bash
# Check login attempts (if web UI enabled)
grep "login" data/logs/app.log | grep -i "failed"

# Review configuration changes
grep "config" data/logs/app.log
```

**Update passwords**:
- [ ] Change camera passwords
- [ ] Change web interface password (if enabled)
- [ ] Rotate encryption keys (if used)

**Security scan**:
```bash
# Scan for vulnerabilities
pip install safety
safety check

# Check for security issues in code
pip install bandit
bandit -r src/
```

### 4.2 System Health Check

**Complete system test**:
```bash
# Run full test suite
pytest

# Run end-to-end test
python scripts/e2e_test.py --duration 300

# Run stress test
python scripts/stress_test.py --duration 600
```

**Hardware inspection**:
- [ ] Check laptop temperature (clean vents if dusty)
- [ ] Verify UPS battery health (if applicable)
- [ ] Test UPS by unplugging (brief test)
- [ ] Check network switch operation
- [ ] Verify speaker functionality

### 4.3 Capacity Planning

**Review storage trends**:
```bash
# Database growth rate
ls -lh data/events.db
# Compare with previous months

# Snapshot storage usage
du -sh data/snapshots/
```

**Review performance trends**:
```bash
# Extract FPS from logs over time
grep "FPS=" data/logs/app.log | tail -100

# Plot resource usage (if monitoring enabled)
python scripts/plot_metrics.py --days 90
```

**Plan for growth**:
- If adding cameras, estimate resource needs
- If storage approaching limit, plan cleanup or expansion
- If performance degrading, plan hardware upgrade

---

## 5. Common Maintenance Tasks

### 5.1 Restart System

**Graceful restart**:
```bash
# If using systemd
sudo systemctl restart smart-cctv

# Or manual
pkill -TERM -f main.py
sleep 5
python src/main.py --config config/config.yaml &
```

**Force restart** (if hung):
```bash
pkill -KILL -f main.py
python src/main.py --config config/config.yaml &
```

### 5.2 Adjust Alert Rules

**Edit alert configuration**:
```bash
nano config/config.yaml
# Modify alert_rules section

# Validate configuration
python scripts/validate_config.py config/config.yaml

# Restart system to apply changes
sudo systemctl restart smart-cctv
```

### 5.3 Add/Remove Cameras

**Add new camera**:
1. Install and configure camera hardware
2. Add camera entry to `config/config.yaml`:
```yaml
cameras:
  - id: "camera_5"
    name: "New Camera"
    url: "rtsp://admin:password@192.168.1.105:554/stream1"
    enabled: true
    fps: 25
```
3. Calibrate camera (optional but recommended):
```bash
python scripts/calibrate_camera.py --camera camera_5
```
4. Restart system

**Remove camera**:
1. Set `enabled: false` in configuration
2. Restart system
3. Optionally delete camera entry from config

### 5.4 Update Alert Thresholds

**If too many false positives**:
- Increase confidence threshold: `processing.detection.confidence_threshold`
- Increase alert cooldown: `alert_rules[].cooldown`
- Adjust distance thresholds: `alert_rules[].conditions.distance_to_reference.value`

**If missing detections**:
- Decrease confidence threshold (carefully)
- Check camera positioning
- Improve lighting
- Re-calibrate camera

### 5.5 Manage Snapshots

**View recent snapshots**:
```bash
ls -lt data/snapshots/ | head -20
```

**Delete specific snapshot**:
```bash
rm data/snapshots/2025-01-15/snapshot_123456.jpg
```

**Clean up manually**:
```bash
# Delete snapshots older than X days
find data/snapshots -type f -mtime +7 -delete

# Delete empty directories
find data/snapshots -type d -empty -delete
```

---

## 6. Troubleshooting Common Issues

### 6.1 System Won't Start

**Check logs**:
```bash
tail -50 data/logs/errors.log
```

**Common causes**:
- Configuration error: `python scripts/validate_config.py config/config.yaml`
- Missing dependencies: `pip install -r requirements.txt`
- Port already in use: `lsof -i :5000` (if web UI enabled)
- Permission issues: Check file ownership

**Solution**:
```bash
# Validate config
python scripts/validate_config.py config/config.yaml

# Check dependencies
pip check

# Fix permissions
chmod +x src/main.py
chmod 600 config/config.yaml
```

### 6.2 Camera Not Connecting

**Test camera directly**:
```bash
# Test with ffplay
ffplay rtsp://admin:password@192.168.1.101:554/stream1

# Test with VLC
vlc rtsp://admin:password@192.168.1.101:554/stream1
```

**Common causes**:
- Wrong URL or credentials
- Camera offline/powered off
- Network connectivity issue
- Firewall blocking connection

**Solution**:
```bash
# Ping camera
ping 192.168.1.101

# Check firewall
sudo ufw status

# Verify credentials (login via browser)
# Check camera web interface at http://192.168.1.101
```

### 6.3 High CPU Usage

**Identify cause**:
```bash
# Check which process is using CPU
top -p $(pgrep -f main.py)

# Profile code (if needed)
python -m cProfile -o profile.stats src/main.py
```

**Solutions**:
- Reduce FPS: `performance.fps_limit: 10`
- Use lighter model: `processing.detection.model: yolov8n`
- Reduce input resolution: Add preprocessing step
- Enable frame skipping: `performance.frame_skip: 1`

### 6.4 High Memory Usage

**Check memory consumption**:
```bash
# Overall memory
free -h

# Process memory
ps aux | grep main.py
```

**Solutions**:
- Clear frame buffers regularly
- Reduce frame buffer size
- Delete old tracks more aggressively
- Restart system daily (via cron)

### 6.5 Alerts Not Playing

**Test audio system**:
```bash
# Test wired speaker
python scripts/test_audio.py --speaker living_room

# Test system audio
speaker-test -t wav -c 2
```

**Common causes**:
- Speaker disconnected/powered off
- Wrong audio output device
- Volume muted
- Bluetooth not paired

**Solutions**:
```bash
# Check audio devices
aplay -l  # Linux
# Select correct device in config

# Check volume
alsamixer

# Re-pair Bluetooth speaker
bluetoothctl
> connect AA:BB:CC:DD:EE:FF
```

### 6.6 Database Corruption

**Symptoms**:
- Errors reading/writing database
- System crashes on database access

**Fix**:
```bash
# Check database integrity
sqlite3 data/events.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp ~/backups/events-20250101.db data/events.db

# Or rebuild (loses data)
rm data/events.db
# System will recreate on next start
```

---

## 7. Upgrade Procedures

### 7.1 Software Upgrade

**Backup first**:
```bash
# Backup everything
./scripts/backup_system.sh
```

**Pull updates**:
```bash
# Stop system
sudo systemctl stop smart-cctv

# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations (if any)
python scripts/migrate_database.py

# Start system
sudo systemctl start smart-cctv

# Monitor for issues
tail -f data/logs/app.log
```

### 7.2 Hardware Upgrade

**Adding more RAM**:
- Shutdown system
- Install RAM
- Boot and verify: `free -h`
- Adjust configuration for better performance

**Adding GPU**:
- Install GPU
- Install CUDA toolkit and drivers
- Install GPU-enabled PyTorch:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```
- Change config: `processing.detection.device: cuda:0`
- Restart and verify GPU usage: `nvidia-smi`

**Upgrading storage**:
- Add external drive
- Mount drive: `sudo mount /dev/sdb1 /mnt/storage`
- Update config paths to use new storage
- Move existing data: `rsync -av data/ /mnt/storage/data/`

---

## 8. Monitoring and Alerts

### 8.1 System Health Monitoring

**Create health check script**:
```bash
#!/bin/bash
# scripts/health_check.sh

# Check if process running
if ! pgrep -f main.py > /dev/null; then
    echo "ERROR: System not running!"
    # Send email alert or restart
    sudo systemctl start smart-cctv
fi

# Check disk space
DISK_USAGE=$(df -h data/ | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage at ${DISK_USAGE}%"
fi

# Check camera connectivity
python scripts/test_cameras.py --quiet || echo "ERROR: Camera connectivity issue"
```

**Schedule via cron**:
```bash
# Edit crontab
crontab -e

# Add health check (runs every 15 minutes)
*/15 * * * * /opt/smart-cctv-system/scripts/health_check.sh >> /var/log/smart-cctv-health.log 2>&1
```

### 8.2 Email Alerts for Issues

**Configure email alerts**:
```python
# Add to config
monitoring:
  email_alerts_enabled: true
  email_to: "your@email.com"
  email_from: "cctv@yourdomain.com"
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
```

---

## 9. Documentation Updates

### 9.1 Maintain Change Log

**CHANGELOG.md**:
```markdown
# Changelog

## [1.1.0] - 2025-02-01
### Added
- Support for 8 cameras
- Email alert notifications

### Changed
- Improved detection accuracy
- Updated YOLO to v8.1

### Fixed
- Memory leak in tracker
- Bluetooth reconnection issue
```

### 9.2 Document Configuration Changes

Keep notes on any configuration tuning:
```
# Configuration Changes Log

2025-01-15: Reduced FPS from 15 to 12 due to CPU usage
2025-01-20: Increased alert cooldown to 60s (was 30s) - too many alerts
2025-01-25: Changed detection threshold from 0.5 to 0.6 - fewer false positives
```

---

## 10. Long-Term Maintenance (Annually)

### 10.1 Full System Review

- [ ] Review all documentation, update as needed
- [ ] Review all alert rules, optimize
- [ ] Review camera placements, adjust if needed
- [ ] Test disaster recovery (restore from backup)
- [ ] Update runbooks and procedures
- [ ] Train any new users

### 10.2 Hardware Refresh

- [ ] Evaluate laptop performance, consider upgrade
- [ ] Replace UPS battery (typically 3-5 year lifespan)
- [ ] Evaluate camera upgrades (higher resolution, better night vision)
- [ ] Consider edge computing devices (Jetson, Coral)

### 10.3 System Evolution

- [ ] Review new features in YOLO/detection models
- [ ] Consider adding new capabilities (facial recognition, LPR)
- [ ] Evaluate cloud integration options
- [ ] Plan for mobile app development

---

## 11. Maintenance Schedule Summary

| Task | Frequency | Estimated Time |
|------|-----------|---------------|
| Check logs | Daily | 5 min |
| Verify cameras | Daily | 2 min |
| Review alerts | Daily | 5 min |
| Log analysis | Weekly | 15 min |
| Database vacuum | Weekly | 5 min |
| Disk cleanup | Weekly | 5 min |
| System updates | Monthly | 30 min |
| Camera maintenance | Monthly | 20 min |
| Backup system | Monthly | 10 min |
| Performance review | Monthly | 30 min |
| Security audit | Quarterly | 60 min |
| Full system test | Quarterly | 90 min |
| Hardware inspection | Quarterly | 30 min |
| Complete review | Annually | 4 hours |

---

## 12. Emergency Procedures

### System Failure
1. Check if process crashed: `systemctl status smart-cctv`
2. Check logs for errors: `tail -100 data/logs/errors.log`
3. Attempt restart: `sudo systemctl restart smart-cctv`
4. If persists, restore from backup
5. Document issue and root cause

### Data Loss
1. Stop system immediately
2. Assess what data was lost
3. Restore from most recent backup
4. Review backup procedures
5. Implement additional safeguards

### Security Breach
1. Disconnect system from network
2. Change all passwords
3. Review logs for unauthorized access
4. Scan for malware
5. Restore from clean backup
6. Implement additional security measures

---

This maintenance guide ensures the system remains operational, secure, and performant over its lifetime. Regular maintenance prevents issues and extends system longevity.
