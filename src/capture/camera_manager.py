"""
Camera Manager - Handles multiple camera connections and frame capture.
"""
import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from queue import Queue, Full
import cv2

from loguru import logger


@dataclass
class Frame:
    """Frame data structure."""
    camera_id: str
    timestamp: float
    image: any  # numpy array
    resolution: tuple
    frame_number: int


class CameraStream:
    """Individual camera stream handler."""
    
    def __init__(self, camera_config: dict):
        """
        Initialize camera stream.
        
        Args:
            camera_config: Camera configuration dictionary
        """
        self.id = camera_config['id']
        self.name = camera_config['name']
        self.url = camera_config['url']
        self.enabled = camera_config.get('enabled', True)
        self.fps = camera_config.get('fps', 25)
        
        self.cap = None
        self.thread = None
        self.running = False
        self.frame_queue = Queue(maxsize=10)
        self.frame_number = 0
        self.last_frame_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        logger.info(f"Initialized camera stream: {self.name} ({self.id})")
    
    def start(self):
        """Start camera capture thread."""
        if not self.enabled:
            logger.info(f"Camera {self.name} is disabled, skipping")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started capture thread for {self.name}")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        while self.running:
            try:
                # Connect to camera if not connected
                if self.cap is None or not self.cap.isOpened():
                    self._connect()
                    if self.cap is None:
                        time.sleep(5)  # Wait before retry
                        continue
                
                # Read frame
                ret, image = self.cap.read()
                
                if not ret or image is None:
                    logger.warning(f"Failed to read frame from {self.name}")
                    self._reconnect()
                    continue
                
                # Create frame object
                frame = Frame(
                    camera_id=self.id,
                    timestamp=time.time(),
                    image=image,
                    resolution=(image.shape[1], image.shape[0]),
                    frame_number=self.frame_number
                )
                
                # Add to queue (non-blocking)
                try:
                    self.frame_queue.put(frame, block=False)
                    self.frame_number += 1
                    self.last_frame_time = time.time()
                    self.reconnect_attempts = 0  # Reset on success
                except Full:
                    # Queue full, drop frame
                    pass
                
                # Frame rate control
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                logger.error(f"Error in capture loop for {self.name}: {e}")
                self._reconnect()
                time.sleep(1)
    
    def _connect(self):
        """Connect to camera stream."""
        try:
            logger.info(f"Connecting to {self.name} at {self.url}")
            self.cap = cv2.VideoCapture(self.url)
            
            if self.cap.isOpened():
                logger.success(f"Connected to {self.name}")
                return True
            else:
                logger.error(f"Failed to connect to {self.name}")
                self.cap = None
                return False
        except Exception as e:
            logger.error(f"Exception connecting to {self.name}: {e}")
            self.cap = None
            return False
    
    def _reconnect(self):
        """Reconnect to camera after failure."""
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnect attempts reached for {self.name}, giving up")
            self.running = False
            return
        
        logger.warning(f"Reconnecting to {self.name} (attempt {self.reconnect_attempts})")
        time.sleep(2)
    
    def get_frame(self) -> Optional[Frame]:
        """
        Get latest frame from queue.
        
        Returns:
            Frame object or None if queue is empty
        """
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        return None
    
    def is_active(self) -> bool:
        """Check if camera is actively producing frames."""
        return (self.running and 
                self.cap is not None and 
                time.time() - self.last_frame_time < 5.0)
    
    def stop(self):
        """Stop camera capture."""
        logger.info(f"Stopping camera {self.name}")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()


class CameraManager:
    """Manages multiple camera streams."""
    
    def __init__(self, config):
        """
        Initialize camera manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.cameras: Dict[str, CameraStream] = {}
        
        # Load camera configurations
        camera_configs = config.get("cameras", [])
        
        for cam_config in camera_configs:
            camera = CameraStream(cam_config)
            self.cameras[camera.id] = camera
        
        logger.info(f"Camera manager initialized with {len(self.cameras)} cameras")
    
    def start(self):
        """Start all cameras."""
        logger.info("Starting all cameras...")
        
        for camera in self.cameras.values():
            camera.start()
            
        # Wait a bit for cameras to connect
        time.sleep(2)
        
        active = self.active_count()
        logger.success(f"Camera manager started: {active}/{len(self.cameras)} cameras active")
    
    def get_frames(self) -> List[Frame]:
        """
        Get latest frames from all cameras.
        
        Returns:
            List of Frame objects
        """
        frames = []
        
        for camera in self.cameras.values():
            frame = camera.get_frame()
            if frame:
                frames.append(frame)
        
        return frames
    
    def active_count(self) -> int:
        """Get count of active cameras."""
        return sum(1 for cam in self.cameras.values() if cam.is_active())
    
    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        """Get specific camera by ID."""
        return self.cameras.get(camera_id)
    
    def stop(self):
        """Stop all cameras."""
        logger.info("Stopping all cameras...")
        
        for camera in self.cameras.values():
            camera.stop()
        
        logger.success("All cameras stopped")
