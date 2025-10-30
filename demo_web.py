#!/usr/bin/env python3
"""
Smart CCTV System - Web Interface Demo
Demonstrates the web interface with sample data.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.web_interface import app, socketio, init_database, DatabaseManager
from src.utils.config_loader import ConfigLoader

def create_demo_data():
    """Create sample data for demonstration."""
    print("📊 Creating demo data...")
    
    db_manager = DatabaseManager()
    
    # Create sample alerts
    sample_alerts = [
        {
            'camera_id': 'camera_1',
            'camera_name': 'Front Door',
            'alert_type': 'person_detected',
            'confidence': 0.95,
            'message': 'Person detected with high confidence',
            'snapshot_path': '/data/snapshots/demo_person.jpg'
        },
        {
            'camera_id': 'camera_2', 
            'camera_name': 'Back Yard',
            'alert_type': 'motion_detected',
            'confidence': 0.78,
            'message': 'Motion detected in monitoring zone',
            'snapshot_path': '/data/snapshots/demo_motion.jpg'
        },
        {
            'camera_id': 'camera_1',
            'camera_name': 'Front Door',
            'alert_type': 'car_detected',
            'confidence': 0.89,
            'message': 'Vehicle detected in driveway',
            'snapshot_path': '/data/snapshots/demo_car.jpg'
        }
    ]
    
    for alert in sample_alerts:
        db_manager.add_alert(**alert)
    
    print("✅ Demo data created successfully")

def create_demo_config():
    """Create demo configuration if none exists."""
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    
    if not config_path.exists():
        print("📝 Creating demo configuration...")
        
        # Copy from example
        example_path = config_path.parent / 'config.example.yaml'
        if example_path.exists():
            import shutil
            shutil.copy(example_path, config_path)
            print(f"✅ Configuration created: {config_path}")
        else:
            print("⚠️  Example configuration not found")

def demo_real_time_updates():
    """Send demo real-time updates via WebSocket."""
    time.sleep(5)  # Wait for web interface to start
    
    import random
    
    print("📡 Starting demo real-time updates...")
    
    while True:
        try:
            # Simulate system stats
            stats = {
                'cpu': random.randint(20, 80),
                'memory': random.randint(50, 90),
                'disk': random.randint(30, 70),
                'temperature': random.randint(45, 75)
            }
            
            socketio.emit('system_stats', stats)
            
            # Occasionally send a demo alert
            if random.random() < 0.1:  # 10% chance
                alert = {
                    'id': random.randint(1000, 9999),
                    'camera_name': random.choice(['Front Door', 'Back Yard', 'Side Gate']),
                    'alert_type': random.choice(['person_detected', 'motion_detected', 'car_detected']),
                    'confidence': round(random.uniform(0.7, 0.99), 2),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'acknowledged': False
                }
                
                socketio.emit('new_alert', alert)
                print(f"📢 Demo alert sent: {alert['alert_type']} at {alert['camera_name']}")
            
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            print(f"Error in demo updates: {e}")
            time.sleep(10)

def main():
    """Main demo function."""
    print("🎬 Smart CCTV System - Web Interface Demo")
    print("=" * 50)
    
    try:
        # Create demo configuration
        create_demo_config()
        
        # Initialize database
        print("📊 Initializing database...")
        init_database()
        
        # Create demo data
        create_demo_data()
        
        # Start real-time updates in background
        update_thread = threading.Thread(target=demo_real_time_updates, daemon=True)
        update_thread.start()
        
        print()
        print("🌟 Demo Features:")
        print("   • Sample security alerts")
        print("   • Real-time system metrics")
        print("   • Interactive dashboard")
        print("   • Configuration management")
        print("   • Mobile-responsive design")
        print()
        print("🎯 Demo Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("📱 Access demo at: http://localhost:5000")
        print("⏰ Real-time updates will start in 5 seconds...")
        print()
        
        # Start web interface
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped")
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == '__main__':
    main()