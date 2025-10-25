# Security and Privacy Best Practices

## 1. Security Principles

### Core Security Goals
1. **Confidentiality**: Protect camera feeds and recorded data from unauthorized access
2. **Integrity**: Ensure data hasn't been tampered with
3. **Availability**: System remains operational and recoverable
4. **Privacy**: Respect privacy of residents and visitors

### Threat Model

**Potential Threats**:
- Unauthorized access to camera feeds
- Interception of network traffic
- Malware/ransomware attacks
- Physical theft of laptop
- Insider threats (family members)
- Data breaches
- Privacy violations

**Attack Vectors**:
- Network vulnerabilities
- Weak passwords
- Unpatched software
- Physical access
- Social engineering

---

## 2. Network Security

### 2.1 Camera Network Isolation

**VLAN Configuration** (Recommended):
```
Internet ← Router ← [VLAN 1: Home Network]
                  ← [VLAN 2: Camera Network]
```

**Benefits**:
- Cameras can't access internet directly
- Cameras can't access other home devices
- Compromised camera can't spread malware

**Implementation**:
```
Router Configuration:
- VLAN 1 (Home): 192.168.1.0/24
- VLAN 2 (Cameras): 192.168.2.0/24
- Firewall rule: Block VLAN 2 → VLAN 1
- Firewall rule: Allow VLAN 1 → VLAN 2 (for viewing)
```

### 2.2 Firewall Configuration

**Laptop Firewall** (UFW on Ubuntu):
```bash
# Enable firewall
sudo ufw enable

# Deny all incoming by default
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Allow web interface (if enabled)
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Allow camera subnet
sudo ufw allow from 192.168.2.0/24

# Check status
sudo ufw status verbose
```

### 2.3 Camera Security

**Camera Hardening Checklist**:
- [ ] Change default admin password (use strong password)
- [ ] Disable unnecessary services (FTP, Telnet, UPnP)
- [ ] Disable cloud access if not needed
- [ ] Update camera firmware to latest version
- [ ] Disable remote access (P2P, DDNS)
- [ ] Use WPA3 (or WPA2) for WiFi cameras
- [ ] Enable HTTPS for camera web interface
- [ ] Disable audio recording if not needed

**Strong Password Requirements**:
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- Unique per camera

**Example Password Generation**:
```bash
# Generate strong password
openssl rand -base64 24
```

### 2.4 Secure Credentials Storage

**DO NOT** store passwords in config files in plaintext!

**Use encryption**:

```yaml
# config/config.yaml
cameras:
  - id: "camera_1"
    url: "rtsp://admin:{{CAMERA_1_PASSWORD}}@192.168.2.101/stream"
```

**Store encrypted credentials**:
```bash
# Create encrypted credentials file
python scripts/encrypt_credentials.py

# System will decrypt at runtime using master key
```

**Use environment variables**:
```bash
export CAMERA_1_PASSWORD="YourSecurePassword123!"
export CAMERA_2_PASSWORD="AnotherSecurePassword456#"
```

---

## 3. System Security

### 3.1 Operating System Hardening

**Ubuntu/Linux**:
```bash
# Keep system updated
sudo apt update && sudo apt upgrade -y

# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# Disable root login via SSH
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Install and configure fail2ban (brute force protection)
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

**Disable unnecessary services**:
```bash
# List services
systemctl list-unit-files --type=service

# Disable unused services
sudo systemctl disable bluetooth.service  # If not using Bluetooth
sudo systemctl disable cups.service       # If not printing
```

### 3.2 Application Security

**Run as non-root user**:
```bash
# Create dedicated user
sudo useradd -r -s /bin/false smartcctv

# Set ownership
sudo chown -R smartcctv:smartcctv /opt/smart-cctv-system

# Run as service under this user
```

**File Permissions**:
```bash
# Restrict config files
chmod 600 config/config.yaml
chmod 600 config/credentials.enc

# Restrict database
chmod 600 data/events.db

# Make scripts executable
chmod +x scripts/*.py
```

**Virtual Environment Isolation**:
```bash
# Always use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Web Interface Security

**If enabling web dashboard**:

**Authentication**:
```python
# Use strong password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Store hashed password in config
password_hash = generate_password_hash("YourStrongPassword123!")
```

**HTTPS/TLS**:
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365

# Configure Flask to use HTTPS
```

```python
# In web_server.py
app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
```

**Session Security**:
```python
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Use strong random key
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
```

**Rate Limiting**:
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic
```

**Content Security Policy**:
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## 4. Data Security

### 4.1 Data Encryption

**Encryption at Rest**:
```bash
# Encrypt snapshots directory
sudo apt install encfs

# Mount encrypted directory
encfs ~/.encrypted/snapshots data/snapshots
```

**Database Encryption**:
```python
# Use SQLCipher instead of SQLite for encrypted database
import sqlite3

# Connect with encryption key
conn = sqlite3.connect('data/events.db')
conn.execute("PRAGMA key = 'your-encryption-key'")
```

### 4.2 Data Retention and Cleanup

**Automatic cleanup** (prevent disk filling):
```python
# In database.py
def cleanup_old_data(self, retention_days=30):
    cutoff = time.time() - (retention_days * 86400)
    self.cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))
    self.conn.commit()
```

**Secure deletion**:
```bash
# Securely delete old files
sudo apt install secure-delete
srm -r data/snapshots/old/
```

### 4.3 Backup and Recovery

**Regular backups**:
```bash
# Backup script (run daily via cron)
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backup/smart-cctv"

# Backup database
cp data/events.db "$BACKUP_DIR/events-$DATE.db"

# Backup configuration
tar -czf "$BACKUP_DIR/config-$DATE.tar.gz" config/

# Keep only last 30 days
find "$BACKUP_DIR" -type f -mtime +30 -delete
```

**Encrypted backups**:
```bash
# Encrypt backup
tar -czf - data/ | openssl enc -aes-256-cbc -salt -out backup.tar.gz.enc
```

---

## 5. Privacy Protection

### 5.1 Privacy Principles

**Minimize data collection**:
- Don't record continuous video (only snapshots on events)
- Don't record audio unless necessary
- Delete old data automatically
- Don't use facial recognition (in MVP)

**Transparency**:
- Inform visitors about surveillance (signs)
- Family members should know about system
- Document what data is collected

**Purpose limitation**:
- Use data only for security purposes
- Don't share data externally
- Don't use for commercial purposes

### 5.2 Privacy Controls

**Configuration options**:
```yaml
privacy:
  record_snapshots: true         # Save images on alerts
  record_continuous: false       # Don't record continuously
  record_audio: false            # Disable audio recording
  blur_faces: false              # Enable if needed
  retention_days: 7              # Keep snapshots for 7 days only
  share_data: false              # Never share externally
```

**Privacy zones** (areas not to monitor):
```yaml
cameras:
  - id: "camera_1"
    privacy_zones:
      - name: "neighbor_window"
        polygon: [[1500, 200], [1800, 200], [1800, 600], [1500, 600]]
        action: "blur"  # or "ignore"
```

### 5.3 Legal Compliance

**Considerations** (consult local laws):
- **Recording laws**: Check if audio recording is legal in your area
- **Surveillance laws**: Some areas require visible signs
- **Privacy laws**: GDPR (EU), CCPA (California), etc.
- **Data protection**: Secure storage requirements
- **Retention limits**: Maximum data retention periods

**Best practices**:
- Post visible "Video Surveillance" signs
- Don't point cameras at public areas unnecessarily
- Don't point cameras at neighbor's property
- Inform guests about surveillance
- Have clear policy on data access

---

## 6. Logging and Monitoring

### 6.1 Security Logging

**What to log**:
- System start/stop events
- Camera connections/disconnections
- Failed login attempts (web UI)
- Configuration changes
- Alert triggers
- Errors and exceptions

**Log security events**:
```python
logger.warning(f"Failed login attempt from {ip_address}")
logger.critical("Unauthorized access attempt detected")
```

**Log retention**:
```yaml
logging:
  security_logs_retention_days: 90
  audit_logs_retention_days: 365
```

### 6.2 Intrusion Detection

**Monitor for anomalies**:
```python
# Alert on suspicious patterns
if failed_logins > 5:
    send_security_alert("Multiple failed login attempts")

if camera_disconnections > 10:
    send_security_alert("Unusual number of camera disconnections")
```

**System monitoring**:
```bash
# Monitor system for suspicious processes
ps aux | grep -v smartcctv
```

---

## 7. Physical Security

### 7.1 Hardware Protection

**Laptop security**:
- Lock laptop in secure location
- Enable BIOS password
- Enable full disk encryption (LUKS, BitLocker, FileVault)
- Use cable lock if accessible location
- Enable screen lock (auto-lock after 5 minutes)

**Camera security**:
- Mount cameras out of reach
- Use tamper-resistant screws
- Enclose wiring in conduit
- Position to avoid being disabled

**Network equipment**:
- Lock router/switch in cabinet
- Disable physical reset buttons if possible
- Use UPS with surge protection

### 7.2 Access Control

**Physical access**:
- Limit who has physical access to laptop
- Keep laptop room locked
- Don't leave laptop unattended and unlocked

**Password policy**:
- Strong laptop login password
- Auto-lock after inactivity
- Different passwords for different services
- Use password manager

---

## 8. Incident Response

### 8.1 Incident Response Plan

**If system compromised**:

1. **Isolate** - Disconnect from network immediately
2. **Assess** - Determine what was compromised
3. **Contain** - Prevent further damage
4. **Eradicate** - Remove threat
5. **Recover** - Restore from backup
6. **Learn** - Update security measures

### 8.2 Emergency Procedures

**System breach checklist**:
- [ ] Disconnect system from network
- [ ] Change all passwords
- [ ] Review logs for unauthorized access
- [ ] Scan for malware
- [ ] Restore from clean backup
- [ ] Update all software
- [ ] Review and strengthen security

**Data breach checklist**:
- [ ] Assess what data was exposed
- [ ] Notify affected individuals (if personal data)
- [ ] Report to authorities if required by law
- [ ] Implement additional safeguards
- [ ] Document incident for future reference

---

## 9. Security Checklist

### Initial Setup
- [ ] Change all default passwords
- [ ] Enable firewall
- [ ] Update all software/firmware
- [ ] Disable unnecessary services
- [ ] Configure network isolation (VLAN)
- [ ] Encrypt sensitive data
- [ ] Set strong web UI password
- [ ] Enable HTTPS for web interface

### Ongoing Maintenance
- [ ] Apply security updates monthly
- [ ] Review logs weekly
- [ ] Test backups monthly
- [ ] Rotate passwords quarterly
- [ ] Review camera access annually
- [ ] Update incident response plan annually

### Compliance
- [ ] Post surveillance signs
- [ ] Inform household members
- [ ] Document data handling procedures
- [ ] Review privacy policy
- [ ] Verify legal compliance

---

## 10. Security Resources

### Recommended Reading
- OWASP Top 10 Security Risks
- NIST Cybersecurity Framework
- CIS Controls
- Local surveillance laws

### Tools
- **nmap** - Network scanning
- **Wireshark** - Network analysis
- **fail2ban** - Brute force protection
- **rkhunter** - Rootkit detection
- **ClamAV** - Antivirus

### Security Audits
Perform regular security audits:
```bash
# Check for open ports
nmap -sT -O localhost

# Check for vulnerabilities
sudo apt install lynis
sudo lynis audit system
```

---

## 11. Privacy by Design

### Principles
1. **Proactive not reactive** - Security built-in from start
2. **Privacy as default** - Most privacy-protective settings
3. **Privacy embedded** - Core functionality, not add-on
4. **Full functionality** - No unnecessary trade-offs
5. **End-to-end security** - Throughout entire lifecycle
6. **Visibility and transparency** - Clear how system works
7. **Respect for user privacy** - User-centric approach

### Implementation
- Local processing (no cloud)
- Minimal data collection
- Automatic data deletion
- Encrypted storage
- No third-party access
- User control over settings
- Clear documentation

---

This security guide should be reviewed and updated regularly as threats evolve and new vulnerabilities are discovered. **Security is an ongoing process, not a one-time setup.**
