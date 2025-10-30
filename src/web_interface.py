"""
Smart CCTV System - Web Interface
Main Flask application for configuration management and monitoring dashboard.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
import os
import yaml
import json
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from functools import wraps
from typing import Dict, List, Any
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'smart-cctv-system-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration paths
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "events.db"

class ConfigManager:
    """Handle configuration file operations."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            else:
                # Use example config if main config doesn't exist
                example_path = self.config_path.parent / "config.example.yaml"
                if example_path.exists():
                    with open(example_path, 'r') as f:
                        self._config = yaml.safe_load(f)
                else:
                    self._config = self._get_default_config()
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return self._config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = self._get_default_config()
            return self._config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to YAML file."""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            self._config = config
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        if self._config is None:
            self.load_config()
        return self._config or {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "system": {
                "name": "Smart CCTV System",
                "log_level": "INFO",
                "data_dir": "./data",
                "models_dir": "./models"
            },
            "cameras": [],
            "processing": {
                "detection": {
                    "model": "yolov8n",
                    "device": "cpu",
                    "confidence_threshold": 0.5,
                    "nms_threshold": 0.4
                }
            },
            "ui": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 5000,
                "auth_enabled": False
            }
        }

class DatabaseManager:
    """Handle database operations for alerts and events."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        camera_id TEXT NOT NULL,
                        camera_name TEXT,
                        alert_type TEXT NOT NULL,
                        object_class TEXT,
                        confidence REAL,
                        distance REAL,
                        priority TEXT DEFAULT 'medium',
                        message TEXT,
                        snapshot_path TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create system_status table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        camera_status TEXT,
                        active_alerts INTEGER DEFAULT 0
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def add_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Add new alert to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts (camera_id, camera_name, alert_type, object_class, 
                                      confidence, distance, priority, message, snapshot_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_data.get('camera_id'),
                    alert_data.get('camera_name'),
                    alert_data.get('alert_type'),
                    alert_data.get('object_class'),
                    alert_data.get('confidence'),
                    alert_data.get('distance'),
                    alert_data.get('priority', 'medium'),
                    alert_data.get('message'),
                    alert_data.get('snapshot_path')
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add alert: {e}")
            return False
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM alerts 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
    
    def get_alerts_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get alerts within date range."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM alerts 
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                ''', (start_date, end_date))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get alerts by date range: {e}")
            return []

# Initialize managers
config_manager = ConfigManager(CONFIG_PATH)
db_manager = DatabaseManager(DB_PATH)

def login_required(f):
    """Decorator for routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        config = config_manager.get_config()
        if config.get('ui', {}).get('auth_enabled', False):
            if 'authenticated' not in session:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health')
def health_check():
    """Health check endpoint for Docker and monitoring."""
    try:
        # Check database connection
        db_manager.get_recent_alerts(1)
        
        # Check configuration
        config = config_manager.get_config()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'services': {
                'database': 'connected',
                'config': 'loaded',
                'web_interface': 'running'
            }
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    config = config_manager.get_config()
    
    if not config.get('ui', {}).get('auth_enabled', False):
        session['authenticated'] = True
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        ui_config = config.get('ui', {})
        if (username == ui_config.get('username', 'admin') and 
            password == ui_config.get('password', 'changeme')):
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Main dashboard page."""
    recent_alerts = db_manager.get_recent_alerts(10)
    config = config_manager.get_config()
    
    # Get camera status
    cameras = config.get('cameras', [])
    camera_status = {
        'total': len(cameras),
        'active': len([c for c in cameras if c.get('enabled', False)]),
        'inactive': len([c for c in cameras if not c.get('enabled', False)])
    }
    
    return render_template('dashboard.html', 
                         alerts=recent_alerts,
                         camera_status=camera_status,
                         config=config)

@app.route('/config')
@login_required
def config_page():
    """Configuration management page."""
    config = config_manager.get_config()
    return render_template('config.html', config=config)

@app.route('/alerts')
@login_required
def alerts_page():
    """Alerts management page."""
    # Get date range from query params
    start_date = request.args.get('start_date', 
                                 (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    alerts = db_manager.get_alerts_by_date_range(start_date, end_date)
    
    return render_template('alerts.html', 
                         alerts=alerts,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/cameras')
@login_required
def cameras_page():
    """Camera management and live feed page."""
    config = config_manager.get_config()
    cameras = config.get('cameras', [])
    return render_template('cameras.html', cameras=cameras)

@app.route('/system')
@login_required
def system_page():
    """System monitoring and logs page."""
    return render_template('system.html')

# API Routes
@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    """Get current configuration via API."""
    return jsonify(config_manager.get_config())

@app.route('/api/config', methods=['POST'])
@login_required
def save_config():
    """Save configuration via API."""
    try:
        new_config = request.get_json()
        if config_manager.save_config(new_config):
            return jsonify({'success': True, 'message': 'Configuration saved successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get alerts via API."""
    limit = int(request.args.get('limit', 50))
    alerts = db_manager.get_recent_alerts(limit)
    return jsonify(alerts)

@app.route('/api/alerts', methods=['POST'])
@login_required
def add_alert():
    """Add new alert via API."""
    try:
        alert_data = request.get_json()
        if db_manager.add_alert(alert_data):
            # Emit real-time alert to connected clients
            socketio.emit('new_alert', alert_data)
            return jsonify({'success': True, 'message': 'Alert added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add alert'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/system/status', methods=['GET'])
@login_required
def get_system_status():
    """Get system status via API."""
    import psutil
    
    status = {
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().isoformat(),
        'active_alerts': len(db_manager.get_recent_alerts(10))
    }
    
    return jsonify(status)

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('status', {'msg': 'Connected to Smart CCTV System'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')

def run_web_interface():
    """Run the web interface."""
    config = config_manager.get_config()
    ui_config = config.get('ui', {})
    
    if not ui_config.get('enabled', False):
        logger.warning("Web interface is disabled in configuration")
        return
    
    host = ui_config.get('host', '0.0.0.0')
    port = ui_config.get('port', 5000)
    
    logger.info(f"Starting web interface on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_web_interface()