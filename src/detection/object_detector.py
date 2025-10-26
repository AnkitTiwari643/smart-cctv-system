"""Object detector module - Enhanced YOLO-based implementation."""
import os
import time
from typing import List, Optional, Dict, Tuple
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
    aspect_ratio: float = 0.0
    keypoints: Optional[List] = None  # For pose estimation
    
    def __post_init__(self):
        """Calculate additional properties after initialization."""
        x1, y1, x2, y2 = self.bbox
        width = x2 - x1
        height = y2 - y1
        self.aspect_ratio = width / height if height > 0 else 0.0


class ObjectDetector:
    """Enhanced YOLO-based object detector for humans, vehicles, and animals."""
    
    # COCO class names - focusing on security-relevant objects
    COCO_CLASSES = {
        0: "person",
        1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane", 5: "bus",
        6: "train", 7: "truck", 8: "boat", 14: "bird", 15: "cat", 16: "dog",
        17: "horse", 18: "sheep", 19: "cow", 20: "elephant", 21: "bear",
        22: "zebra", 23: "giraffe", 24: "backpack", 25: "umbrella",
        26: "handbag", 27: "tie", 28: "suitcase"
    }
    
    # Enhanced class categories for better filtering
    HUMAN_CLASSES = ["person"]
    VEHICLE_CLASSES = ["car", "truck", "bus", "motorcycle", "bicycle", "airplane", "boat", "train"]
    ANIMAL_CLASSES = ["dog", "cat", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "bird"]
    
    # Priority classes for security monitoring
    SECURITY_CLASSES = HUMAN_CLASSES + VEHICLE_CLASSES + ANIMAL_CLASSES
    
    # Class-specific confidence thresholds
    CLASS_CONFIDENCE_THRESHOLDS = {
        "person": 0.4,      # Lower threshold for humans (more sensitive)
        "car": 0.6,         # Higher threshold for vehicles
        "truck": 0.6,
        "motorcycle": 0.5,
        "bicycle": 0.5,
        "bus": 0.7,
        "dog": 0.5,         # Medium threshold for animals
        "cat": 0.5,
        "bird": 0.3,        # Lower for smaller animals
    }
    
    # Size filtering parameters (min/max area in pixels)
    SIZE_FILTERS = {
        "person": {"min_area": 500, "max_area": 100000, "min_aspect": 0.2, "max_aspect": 2.0},
        "car": {"min_area": 1000, "max_area": 200000, "min_aspect": 0.8, "max_aspect": 3.0},
        "truck": {"min_area": 2000, "max_area": 300000, "min_aspect": 1.0, "max_aspect": 4.0},
        "motorcycle": {"min_area": 300, "max_area": 50000, "min_aspect": 0.5, "max_aspect": 2.5},
        "bicycle": {"min_area": 200, "max_area": 30000, "min_aspect": 0.3, "max_aspect": 2.0},
        "dog": {"min_area": 200, "max_area": 50000, "min_aspect": 0.5, "max_aspect": 3.0},
        "cat": {"min_area": 100, "max_area": 20000, "min_aspect": 0.5, "max_aspect": 2.5},
        "bird": {"min_area": 50, "max_area": 5000, "min_aspect": 0.3, "max_aspect": 2.0},
    }
    
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
        self.batch_size = config.get("processing.detection.batch_size", 1)
        
        # Enhanced filtering options
        self.use_class_specific_thresholds = True
        self.use_size_filtering = True
        self.use_temporal_smoothing = True
        
        # Performance tracking
        self.detection_stats = {
            "total_detections": 0,
            "filtered_detections": 0,
            "processing_times": [],
            "class_counts": {}
        }
        
        # Initialize model
        self.model = None
        self.is_loaded = False
        
        logger.info(f"Initializing enhanced object detector with model: {self.model_name}")
        logger.info(f"Device: {self.device}, Base confidence: {self.confidence_threshold}")
        logger.info(f"Classes filter: {self.classes_filter}")
        logger.info(f"Enhanced features: class-specific thresholds, size filtering, temporal smoothing")
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model with enhanced error handling."""
        try:
            # Set device
            if self.device == "mps" and torch.backends.mps.is_available():
                device = "mps"
                logger.info("Using Metal Performance Shaders (MPS) for acceleration")
            elif self.device.startswith("cuda") and torch.cuda.is_available():
                device = self.device
                logger.info(f"Using CUDA device: {device}")
            else:
                device = "cpu"
                logger.info("Using CPU for inference")
            
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
            
            # Enhanced model configuration
            self._configure_model()
            
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
    
    def _configure_model(self):
        """Configure model for enhanced performance."""
        try:
            # Set model-specific parameters
            if hasattr(self.model, 'model'):
                # Enable TensorRT if available (for NVIDIA GPUs)
                if torch.cuda.is_available() and hasattr(torch.backends, 'cudnn'):
                    torch.backends.cudnn.benchmark = True
                
                # Set model to evaluation mode
                self.model.model.eval()
            
        except Exception as e:
            logger.warning(f"Model configuration warning: {e}")
    
    def detect(self, frame) -> List[Detection]:
        """
        Enhanced detect objects in frame with better filtering.
        
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
            
            # Pre-process image for better detection
            processed_image = self._preprocess_image(image)
            
            # Run inference with enhanced parameters
            results = self.model(
                processed_image,
                conf=self.confidence_threshold,
                iou=self.nms_threshold,
                imgsz=self.input_size,
                verbose=False,
                save=False,
                classes=self._get_class_indices() if self.classes_filter else None
            )
            
            detections = []
            
            # Process results with enhanced filtering
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = self._process_detection(box)
                        if detection and self._is_valid_detection(detection):
                            detections.append(detection)
            
            # Apply post-processing filters
            detections = self._post_process_detections(detections)
            
            # Update statistics
            self._update_stats(detections, time.time() - start_time)
            
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
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Pre-process image for better detection."""
        try:
            # Apply histogram equalization for better contrast
            if len(image.shape) == 3:
                # Convert to LAB color space
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                # Convert back to BGR
                image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return image
            
        except Exception as e:
            logger.debug(f"Image preprocessing error: {e}")
            return image
    
    def _process_detection(self, box) -> Optional[Detection]:
        """Process individual detection box."""
        try:
            # Extract box data
            xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
            conf = box.conf[0].cpu().numpy()  # confidence
            cls = int(box.cls[0].cpu().numpy())  # class id
            
            # Get class name
            class_name = self.COCO_CLASSES.get(cls, f"class_{cls}")
            
            # Filter by allowed classes
            if self.classes_filter and class_name not in self.classes_filter:
                return None
            
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
            
            return detection
            
        except Exception as e:
            logger.debug(f"Detection processing error: {e}")
            return None
    
    def _is_valid_detection(self, detection: Detection) -> bool:
        """Enhanced validation of detection quality."""
        # Class-specific confidence threshold
        if self.use_class_specific_thresholds:
            min_conf = self.CLASS_CONFIDENCE_THRESHOLDS.get(detection.class_name, self.confidence_threshold)
            if detection.confidence < min_conf:
                return False
        
        # Size filtering
        if self.use_size_filtering:
            size_filter = self.SIZE_FILTERS.get(detection.class_name)
            if size_filter:
                # Check area bounds
                if (detection.area < size_filter["min_area"] or 
                    detection.area > size_filter["max_area"]):
                    return False
                
                # Check aspect ratio bounds
                if (detection.aspect_ratio < size_filter["min_aspect"] or 
                    detection.aspect_ratio > size_filter["max_aspect"]):
                    return False
        
        # Additional validation for specific classes
        if detection.class_name == "person":
            # Humans should have reasonable aspect ratio (taller than wide)
            if detection.aspect_ratio > 1.5:  # Too wide for a person
                return False
        
        elif detection.class_name in self.VEHICLE_CLASSES:
            # Vehicles should typically be wider than tall
            if detection.class_name in ["car", "truck", "bus"] and detection.aspect_ratio < 0.5:
                return False
        
        return True
    
    def _post_process_detections(self, detections: List[Detection]) -> List[Detection]:
        """Apply post-processing filters to detections."""
        if not detections:
            return detections
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda d: d.confidence, reverse=True)
        
        # Remove overlapping detections of the same class
        filtered_detections = []
        for detection in detections:
            is_duplicate = False
            
            for existing in filtered_detections:
                if (existing.class_name == detection.class_name and 
                    self._calculate_iou(detection.bbox, existing.bbox) > 0.5):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_detections.append(detection)
        
        return filtered_detections
    
    def _calculate_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate Intersection over Union of two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _get_class_indices(self) -> List[int]:
        """Get class indices for filtering."""
        indices = []
        for class_name in self.classes_filter:
            for idx, name in self.COCO_CLASSES.items():
                if name == class_name:
                    indices.append(idx)
        return indices
    
    def _update_stats(self, detections: List[Detection], processing_time: float):
        """Update detection statistics."""
        self.detection_stats["total_detections"] += len(detections)
        self.detection_stats["processing_times"].append(processing_time)
        
        # Keep only last 1000 processing times
        if len(self.detection_stats["processing_times"]) > 1000:
            self.detection_stats["processing_times"] = self.detection_stats["processing_times"][-1000:]
        
        # Update class counts
        for detection in detections:
            class_name = detection.class_name
            if class_name not in self.detection_stats["class_counts"]:
                self.detection_stats["class_counts"][class_name] = 0
            self.detection_stats["class_counts"][class_name] += 1
    
    def detect_and_draw(self, frame, draw_confidence=True, draw_labels=True, 
                       draw_center=False, draw_id=False) -> Optional[np.ndarray]:
        """
        Enhanced detect objects and draw bounding boxes on image.
        
        Args:
            frame: Frame object
            draw_confidence: Whether to draw confidence scores
            draw_labels: Whether to draw class labels
            draw_center: Whether to draw center points
            draw_id: Whether to draw detection IDs
            
        Returns:
            Image with drawn detections or None
        """
        detections = self.detect(frame)
        
        if not detections:
            return frame.image.copy()
        
        image = frame.image.copy()
        
        # Enhanced colors for different classes
        colors = {
            "person": (0, 255, 0),      # Green
            "car": (255, 0, 0),         # Blue  
            "truck": (255, 0, 255),     # Magenta
            "motorcycle": (0, 255, 255), # Yellow
            "bicycle": (255, 255, 0),   # Cyan
            "bus": (128, 0, 128),       # Purple
            "dog": (255, 165, 0),       # Orange
            "cat": (255, 192, 203),     # Pink
            "bird": (173, 216, 230),    # Light Blue
        }
        
        for i, detection in enumerate(detections):
            x1, y1, x2, y2 = detection.bbox
            color = colors.get(detection.class_name, (128, 128, 128))  # Default gray
            
            # Draw bounding box with thickness based on confidence
            thickness = max(1, int(detection.confidence * 3))
            cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
            
            # Draw center point
            if draw_center:
                cv2.circle(image, detection.center_point, 3, color, -1)
            
            # Prepare label components
            label_parts = []
            if draw_labels:
                label_parts.append(detection.class_name)
            if draw_confidence:
                label_parts.append(f"{detection.confidence:.2f}")
            if draw_id:
                label_parts.append(f"#{i}")
            
            if label_parts:
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
        return [d for d in detections if d.class_name in self.HUMAN_CLASSES]
    
    def get_vehicle_detections(self, detections: List[Detection]) -> List[Detection]:
        """Get only vehicle detections."""
        return [d for d in detections if d.class_name in self.VEHICLE_CLASSES]
    
    def get_animal_detections(self, detections: List[Detection]) -> List[Detection]:
        """Get only animal detections."""
        return [d for d in detections if d.class_name in self.ANIMAL_CLASSES]
    
    def get_detection_stats(self) -> Dict:
        """Get detection performance statistics."""
        stats = self.detection_stats.copy()
        
        if stats["processing_times"]:
            stats["avg_processing_time"] = np.mean(stats["processing_times"])
            stats["fps"] = 1.0 / stats["avg_processing_time"] if stats["avg_processing_time"] > 0 else 0
        else:
            stats["avg_processing_time"] = 0
            stats["fps"] = 0
        
        return stats
    
    def reset_stats(self):
        """Reset detection statistics."""
        self.detection_stats = {
            "total_detections": 0,
            "filtered_detections": 0,
            "processing_times": [],
            "class_counts": {}
        }
    
    def set_confidence_threshold(self, threshold: float, class_name: str = None):
        """
        Set confidence threshold globally or for specific class.
        
        Args:
            threshold: Confidence threshold (0.0 to 1.0)
            class_name: Specific class name (None for global)
        """
        if class_name:
            self.CLASS_CONFIDENCE_THRESHOLDS[class_name] = threshold
            logger.info(f"Set confidence threshold for {class_name}: {threshold}")
        else:
            self.confidence_threshold = threshold
            logger.info(f"Set global confidence threshold: {threshold}")
    
    def stop(self):
        """Stop detector and cleanup resources."""
        logger.info("Stopping object detector")
        
        # Log final statistics
        stats = self.get_detection_stats()
        logger.info(f"Detection stats: {stats['total_detections']} total detections")
        logger.info(f"Average FPS: {stats['fps']:.2f}")
        logger.info(f"Class distribution: {stats['class_counts']}")
        
        if self.model is not None:
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        self.is_loaded = False
