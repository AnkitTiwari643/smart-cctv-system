#!/usr/bin/env python3
"""
Smart CCTV System - Complete System Launcher
Starts both the CCTV detection system and web interface.
"""

import sys
import os
import signal
import threading
import time
import subprocess
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Shutting down Smart CCTV System...")
    
    # Terminate all child processes
    for process in processes:
        if process.poll() is None:  # Process is still running
            print(f"   Stopping {process.args[0]}...")
            process.terminate()
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Force kill if still running
    for process in processes:
        if process.poll() is None:
            print(f"   Force killing {process.args[0]}...")
            process.kill()
    
    sys.exit(0)

def start_main_system():
    """Start the main CCTV detection system."""
    try:
        print("🎥 Starting CCTV detection system...")
        main_process = subprocess.Popen([
            sys.executable, 
            str(Path(__file__).parent / 'src' / 'main.py')
        ])
        return main_process
    except Exception as e:
        print(f"❌ Error starting main system: {e}")
        return None

def start_web_interface():
    """Start the web interface."""
    try:
        print("🌐 Starting web interface...")
        web_process = subprocess.Popen([
            sys.executable, 
            str(Path(__file__).parent / 'run_web.py')
        ])
        return web_process
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        return None

def main():
    """Main entry point for complete system."""
    global processes
    processes = []
    
    print("🚀 Smart CCTV System - Complete Startup")
    print("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Check if config exists
        config_path = Path(__file__).parent / 'config' / 'config.yaml'
        if not config_path.exists():
            print("⚠️  Configuration file not found!")
            print(f"   Please copy and configure: {config_path}")
            print(f"   From template: {config_path.parent / 'config.example.yaml'}")
            print()
            print("🌐 Starting web interface only for configuration...")
            
            # Start only web interface for configuration
            web_process = start_web_interface()
            if web_process:
                processes.append(web_process)
                print()
                print("🎯 Access web interface to configure the system:")
                print("   http://localhost:5000")
                print()
                print("   Once configured, restart this script to enable full functionality")
        else:
            # Start main CCTV system
            main_process = start_main_system()
            if main_process:
                processes.append(main_process)
            
            # Start web interface
            web_process = start_web_interface()
            if web_process:
                processes.append(web_process)
            
            print()
            print("✅ System startup complete!")
            print()
            print("🎯 Access points:")
            print("   • Web Interface: http://localhost:5000")
            print("   • Login: admin / admin123")
            print()
            print("📊 Features available:")
            print("   • Live camera feeds")
            print("   • Real-time object detection")
            print("   • Alert management")
            print("   • System monitoring")
            print("   • Configuration management")
        
        if not processes:
            print("❌ No processes started successfully")
            sys.exit(1)
        
        print()
        print("⏰ System running... Press Ctrl+C to stop")
        print()
        
        # Monitor processes
        while True:
            time.sleep(5)
            
            # Check if any process has died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️  Process {process.args[0]} has stopped unexpectedly")
                    
                    # Restart the process
                    if 'main.py' in str(process.args[0]):
                        print("🔄 Restarting main system...")
                        new_process = start_main_system()
                        if new_process:
                            processes[i] = new_process
                    elif 'run_web.py' in str(process.args[0]):
                        print("🔄 Restarting web interface...")
                        new_process = start_web_interface()
                        if new_process:
                            processes[i] = new_process
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ System error: {e}")
    finally:
        signal_handler(signal.SIGTERM, None)

if __name__ == '__main__':
    main()