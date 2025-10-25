"""
Main application entry point for the Smart CCTV System.
"""
import signal
import sys
import time
from pathlib import Path
from typing import List
import argparse

from loguru import logger

from capture.camera_manager import CameraManager
from detection.object_detector import ObjectDetector
from tracking.object_tracker import ObjectTracker
from distance.distance_calculator import DistanceCalculator
from alerts.alert_manager import AlertManager
from utils.config_loader import ConfigLoader
from utils.database import Database


class SmartCCTVSystem:
    """Main application orchestrator."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the Smart CCTV System.
        
        Args:
            config_path: Path to configuration file
        """
        logger.info("Initializing Smart CCTV System...")
        
        # Load configuration
        self.config = ConfigLoader(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize database
        self.db = Database(self.config.get("storage.database_path", "data/events.db"))
        
        # Initialize components
        self.camera_manager = CameraManager(self.config)
        self.detector = ObjectDetector(self.config)
        self.tracker = ObjectTracker(self.config)
        self.distance_calc = DistanceCalculator(self.config)
        self.alert_manager = AlertManager(self.config)
        
        # System state
        self.running = False
        self.frame_count = 0
        self.start_time = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.success("Smart CCTV System initialized successfully")
    
    def _setup_logging(self):
        """Configure logging based on config."""
        log_level = self.config.get("system.log_level", "INFO")
        log_dir = Path(self.config.get("system.data_dir", "data")) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure loguru
        logger.remove()  # Remove default handler
        
        # Console handler
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
            level=log_level,
            colorize=True
        )
        
        # File handler - main log
        logger.add(
            log_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function} | {message}",
            level=log_level,
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )
        
        # File handler - errors only
        logger.add(
            log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function} | {message}",
            level="ERROR",
            rotation="50 MB",
            retention="90 days"
        )
    
    def start(self):
        """Start the system."""
        logger.info("Starting Smart CCTV System...")
        self.running = True
        self.start_time = time.time()
        
        try:
            # Start camera manager
            self.camera_manager.start()
            logger.info(f"Started {len(self.camera_manager.cameras)} cameras")
            
            # Main processing loop
            self._main_loop()
            
        except Exception as e:
            logger.exception(f"Fatal error in main loop: {e}")
            self.stop()
    
    def _main_loop(self):
        """Main processing loop."""
        logger.info("Entering main processing loop")
        fps_limit = self.config.get("performance.fps_limit", 15)
        frame_time = 1.0 / fps_limit if fps_limit > 0 else 0
        
        while self.running:
            loop_start = time.time()
            
            try:
                # Get frames from all cameras
                frames = self.camera_manager.get_frames()
                
                if not frames:
                    time.sleep(0.1)
                    continue
                
                # Process each frame
                for frame in frames:
                    self._process_frame(frame)
                    self.frame_count += 1
                
                # Log stats periodically
                if self.frame_count % 100 == 0:
                    self._log_stats()
                
                # Frame rate limiting
                elapsed = time.time() - loop_start
                if frame_time > elapsed:
                    time.sleep(frame_time - elapsed)
                    
            except Exception as e:
                logger.error(f"Error in main loop iteration: {e}")
                time.sleep(0.1)
    
    def _process_frame(self, frame):
        """
        Process a single frame through the pipeline.
        
        Args:
            frame: Frame object from camera
        """
        try:
            # Step 1: Object detection
            detections = self.detector.detect(frame)
            
            if not detections:
                return
            
            # Step 2: Object tracking
            tracks = self.tracker.update(detections, frame.camera_id)
            
            if not tracks:
                return
            
            # Step 3: Distance calculation (for persons only)
            for track in tracks:
                if track.class_name == "person":
                    distance_info = self.distance_calc.calculate(track, frame.camera_id)
                    track.distance_info = distance_info
            
            # Step 4: Alert evaluation
            self.alert_manager.evaluate(tracks, frame)
            
            # Step 5: Log events
            self._log_events(tracks, frame)
            
        except Exception as e:
            logger.error(f"Error processing frame from {frame.camera_id}: {e}")
    
    def _log_events(self, tracks, frame):
        """Log detection events to database."""
        for track in tracks:
            if track.is_confirmed:
                event_data = {
                    "timestamp": frame.timestamp,
                    "camera_id": frame.camera_id,
                    "event_type": "detection",
                    "track_id": track.track_id,
                    "class_name": track.class_name,
                    "distance": getattr(track, 'distance_info', {}).get('distance_to_camera', None),
                    "alert_triggered": 0,
                    "metadata": {}
                }
                self.db.insert_event(event_data)
    
    def _log_stats(self):
        """Log system statistics."""
        uptime = time.time() - self.start_time
        fps = self.frame_count / uptime if uptime > 0 else 0
        
        logger.info(
            f"Stats: Frames={self.frame_count}, FPS={fps:.2f}, "
            f"Uptime={uptime:.0f}s, Cameras={self.camera_manager.active_count()}"
        )
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully."""
        logger.warning(f"Received signal {sig}, shutting down...")
        self.stop()
    
    def stop(self):
        """Stop the system gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping Smart CCTV System...")
        self.running = False
        
        try:
            # Stop components in reverse order
            self.alert_manager.stop()
            self.distance_calc.stop()
            self.tracker.stop()
            self.detector.stop()
            self.camera_manager.stop()
            
            # Close database
            self.db.close()
            
            logger.success("Smart CCTV System stopped successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smart CCTV System with AI Detection")
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Smart CCTV System v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║     Smart CCTV System with AI Detection          ║
    ║     Real-time Object Detection & Alerts          ║
    ║     Version 1.0.0                                ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    # Create and start system
    system = SmartCCTVSystem(config_path=args.config)
    system.start()


if __name__ == "__main__":
    main()
