"""Object detector module - YOLO-based implementation."""
import os
import time
from typing import List, Optional
from dataclasses import dataclass
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from loguru import logger


@dataclass
class Detection:
    """Detection result data structure."""
    bbox: tuple  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: str
    center_point: tuple  # (x, y)
    area: float


class ObjectDetector:
    """YOLO-based object detector for humans, vehicles, and other objects."""
    
    # COCO class names - focusing on security-relevant objects
    COCO_CLASSES = {
        0: "person",
        1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane", 5: "bus",
        6: "train", 7: "truck", 8: "boat", 14: "bird", 15: "cat", 16: "dog",
        17: "horse", 18: "sheep", 19: "cow", 20: "elephant", 21: "bear",
        22: "zebra", 23: "giraffe", 24: "backpack", 25: "umbrella",
        26: "handbag", 27: "tie", 28: "suitcase"
    }
    
    # Priority classes for security monitoring
    SECURITY_CLASSES = ["person", "car", "truck", "motorcycle", "bus", "bicycle", "dog", "cat"]
    
    def __init__(self, config):
        """Initialize detector with YOLO model."""
        self.config = config
        
        # Get configuration
        self.model_name = config.get("processing.detection.model", "yolov8n")
        self.device = config.get("processing.detection.device", "cpu")
        self.confidence_threshold = config.get("processing.detection.confidence_threshold", 0.5)
        self.nms_threshold = config.get("processing.detection.nms_threshold", 0.4)
        self.input_size = config.get("processing.detection.input_size", [640, 640])
        self.classes_filter = config.get("processing.detection.classes_filter", self.SECURITY_CLASSES)
        
        # Initialize model
        self.model = None
        self.is_loaded = False
        
        logger.info(f"Initializing object detector with model: {self.model_name}")
        logger.info(f"Device: {self.device}, Confidence: {self.confidence_threshold}")
        logger.info(f"Classes filter: {self.classes_filter}")
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model."""
        try:
            # Set device
            if self.device == "mps" and torch.backends.mps.is_available():
                device = "mps"
            elif self.device.startswith("cuda") and torch.cuda.is_available():
                device = self.device
            else:
                device = "cpu"
            
            logger.info(f"Loading {self.model_name} model on device: {device}")
            
            # Set models directory
            models_dir = self.config.get("system.models_dir", "./models")
            os.makedirs(models_dir, exist_ok=True)
            
            # Set YOLO config directory to avoid permission issues
            os.environ['YOLO_CONFIG_DIR'] = models_dir
            
            # Try to load model with better error handling
            model_path = f"{self.model_name}.pt"
            
            try:
                # YOLO will auto-download if model doesn't exist
                logger.info(f"Attempting to load YOLO model: {model_path}")
                self.model = YOLO(model_path)
                self.model.to(device)
                logger.success(f"YOLO model {self.model_name} loaded successfully")
            except Exception as download_error:
                logger.warning(f"Failed to download model online: {download_error}")
                
                # Try to find local model file
                local_model_path = os.path.join(models_dir, model_path)
                if os.path.exists(local_model_path):
                    logger.info(f"Using local model file: {local_model_path}")
                    self.model = YOLO(local_model_path)
                    self.model.to(device)
                    logger.success(f"Local YOLO model {self.model_name} loaded successfully")
                else:
                    logger.error("No local model found and download failed")
                    raise
            
            # Warm up model with dummy input
            try:
                dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
                _ = self.model(dummy_input, verbose=False)
                logger.info("Model warmup completed")
            except Exception as warmup_error:
                logger.warning(f"Model warmup failed: {warmup_error}")
            
            self.is_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            logger.info("Suggestions:")
            logger.info("1. Check internet connection for model download")
            logger.info("2. Try downloading model manually:")
            logger.info(f"   wget https://github.com/ultralytics/assets/releases/download/v8.3.0/{self.model_name}.pt -O models/{self.model_name}.pt")
            logger.info("3. Use a different model (yolov8n, yolov8s, yolov8m, yolov8l)")
            self.is_loaded = False
            raise
    
    def detect(self, frame) -> List[Detection]:
        """
        Detect objects in frame.
        
        Args:
            frame: Frame object with image data
            
        Returns:
            List of Detection objects
        """
        if not self.is_loaded:
            logger.warning("Model not loaded, skipping detection")
            return []
        
        try:
            start_time = time.time()
            
            # Get image from frame
            image = frame.image
            if image is None:
                return []
            
            # Run inference
            results = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.nms_threshold,
                imgsz=self.input_size,
                verbose=False
            )
            
            detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box data
                        xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                        conf = box.conf[0].cpu().numpy()  # confidence
                        cls = int(box.cls[0].cpu().numpy())  # class id
                        
                        # Get class name
                        class_name = self.COCO_CLASSES.get(cls, f"class_{cls}")
                        
                        # Filter by allowed classes
                        if self.classes_filter and class_name not in self.classes_filter:
                            continue
                        
                        # Calculate center point and area
                        x1, y1, x2, y2 = xyxy
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        area = (x2 - x1) * (y2 - y1)
                        
                        # Create detection object
                        detection = Detection(
                            bbox=(int(x1), int(y1), int(x2), int(y2)),
                            confidence=float(conf),
                            class_id=cls,
                            class_name=class_name,
                            center_point=(int(center_x), int(center_y)),
                            area=float(area)
                        )
                        
                        detections.append(detection)
            
            # Log performance
            inference_time = time.time() - start_time
            if len(detections) > 0:
                logger.debug(
                    f"Detected {len(detections)} objects in {inference_time:.3f}s "
                    f"(camera: {frame.camera_id})"
                )
            
            return detections
            
        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return []
    
    def detect_and_draw(self, frame, draw_confidence=True, draw_labels=True) -> Optional[np.ndarray]:
        """
        Detect objects and draw bounding boxes on image.
        
        Args:
            frame: Frame object
            draw_confidence: Whether to draw confidence scores
            draw_labels: Whether to draw class labels
            
        Returns:
            Image with drawn detections or None
        """
        detections = self.detect(frame)
        
        if not detections:
            return frame.image.copy()
        
        image = frame.image.copy()
        
        # Define colors for different classes
        colors = {
            "person": (0, 255, 0),      # Green
            "car": (255, 0, 0),         # Blue  
            "truck": (255, 0, 255),     # Magenta
            "motorcycle": (0, 255, 255), # Yellow
            "bicycle": (255, 255, 0),   # Cyan
            "bus": (128, 0, 128),       # Purple
            "dog": (255, 165, 0),       # Orange
            "cat": (255, 192, 203),     # Pink
        }
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            color = colors.get(detection.class_name, (128, 128, 128))  # Default gray
            
            # Draw bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label and confidence
            if draw_labels or draw_confidence:
                label_parts = []
                if draw_labels:
                    label_parts.append(detection.class_name)
                if draw_confidence:
                    label_parts.append(f"{detection.confidence:.2f}")
                
                label = " ".join(label_parts)
                
                # Calculate label size
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                
                # Draw label background
                cv2.rectangle(image, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
                
                # Draw label text
                cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return image
    
    def get_detections_by_class(self, detections: List[Detection], class_name: str) -> List[Detection]:
        """Get detections filtered by class name."""
        return [d for d in detections if d.class_name == class_name]
    
    def get_human_detections(self, detections: List[Detection]) -> List[Detection]:
        """Get only human detections."""
        return self.get_detections_by_class(detections, "person")
    
    def get_vehicle_detections(self, detections: List[Detection]) -> List[Detection]:
        """Get only vehicle detections."""
        vehicle_classes = ["car", "truck", "motorcycle", "bus", "bicycle"]
        return [d for d in detections if d.class_name in vehicle_classes]
    
    def stop(self):
        """Stop detector and cleanup resources."""
        logger.info("Stopping object detector")
        if self.model is not None:
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self.is_loaded = False
