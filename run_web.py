#!/usr/bin/env python3
"""
Smart CCTV System - Web Interface Launcher
Starts the web-based management interface for the CCTV system.
"""

import sys
import os
import signal
import threading
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.web_interface import app, socketio, init_database
from src.utils.config_loader import ConfigLoader

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Shutting down web interface...")
    sys.exit(0)

def main():
    """Main entry point for web interface."""
    print("🚀 Starting Smart CCTV System Web Interface...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize database
        print("📊 Initializing database...")
        init_database()
        
        # Load configuration
        config_path = Path(__file__).parent / 'config' / 'config.yaml'
        if not config_path.exists():
            config_path = Path(__file__).parent / 'config' / 'config.example.yaml'
        
        config_loader = ConfigLoader(str(config_path))
        config = config_loader.load_config()
        
        # Web interface settings
        web_config = config.get('web_interface', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 5000)
        debug = web_config.get('debug', False)
        
        print(f"🌐 Web interface will be available at: http://{host}:{port}")
        print(f"🔐 Default login: admin / admin123")
        print("📱 Features:")
        print("   • Real-time dashboard")
        print("   • Configuration management")
        print("   • Alert monitoring")
        print("   • Camera feeds")
        print("   • System monitoring")
        print("   • Mobile-responsive UI")
        print()
        print("⚡ Starting server...")
        
        # Start the web application
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        sys.exit(1)
    finally:
        print("👋 Web interface stopped")

if __name__ == '__main__':
    main()