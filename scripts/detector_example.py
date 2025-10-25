#!/usr/bin/env python3
"""
Example usage of the updated Object Detector.
This script demonstrates how to use the YOLO-based detector.
"""
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def example_usage():
    """Demonstrate object detector usage."""
    
    # Import after path setup
    from detection.object_detector import ObjectDetector, Detection
    from utils.config_loader import ConfigLoader
    
    print("🔍 Object Detector Usage Example")
    print("=" * 50)
    
    # 1. Load configuration
    print("\n1. Loading configuration...")
    config = ConfigLoader("config/config.yaml")
    print("   ✓ Configuration loaded")
    
    # 2. Initialize detector
    print("\n2. Initializing YOLO detector...")
    detector = ObjectDetector(config)
    print("   ✓ Detector initialized with YOLO model")
    
    # 3. Show detector capabilities
    print(f"\n3. Detector Configuration:")
    print(f"   • Model: {detector.model_name}")
    print(f"   • Device: {detector.device}")
    print(f"   • Confidence threshold: {detector.confidence_threshold}")
    print(f"   • Classes filter: {detector.classes_filter}")
    
    # 4. Show detection methods
    print(f"\n4. Available Detection Methods:")
    print(f"   • detect(frame) -> List[Detection]")
    print(f"   • detect_and_draw(frame) -> annotated_image")
    print(f"   • get_human_detections(detections)")
    print(f"   • get_vehicle_detections(detections)")
    print(f"   • get_detections_by_class(detections, class_name)")
    
    # 5. Show Detection object structure
    print(f"\n5. Detection Object Structure:")
    print(f"   Detection(")
    print(f"     bbox=(x1, y1, x2, y2),")
    print(f"     confidence=0.95,")
    print(f"     class_id=0,")
    print(f"     class_name='person',")
    print(f"     center_point=(x, y),")
    print(f"     area=1234.5")
    print(f"   )")
    
    # 6. Show supported classes
    print(f"\n6. Supported Object Classes:")
    security_classes = detector.SECURITY_CLASSES
    for i, cls in enumerate(security_classes):
        print(f"   {i+1:2d}. {cls}")
    
    # 7. Example detection workflow
    print(f"\n7. Typical Detection Workflow:")
    print(f"   ```python")
    print(f"   # Get frame from camera")
    print(f"   frame = camera_manager.get_frame()")
    print(f"   ")
    print(f"   # Run detection")
    print(f"   detections = detector.detect(frame)")
    print(f"   ")
    print(f"   # Filter detections")
    print(f"   humans = detector.get_human_detections(detections)")
    print(f"   vehicles = detector.get_vehicle_detections(detections)")
    print(f"   ")
    print(f"   # Process results")
    print(f"   for detection in humans:")
    print(f"       print(f'Human detected: {{detection.confidence:.2f}}')")
    print(f"   ```")
    
    # 8. Performance expectations
    print(f"\n8. Performance Expectations:")
    print(f"   • YOLOv8n (nano): ~50-100 FPS on CPU")
    print(f"   • YOLOv8s (small): ~30-60 FPS on CPU")
    print(f"   • YOLOv8m (medium): ~15-30 FPS on CPU")
    print(f"   • GPU acceleration available with CUDA/MPS")
    
    print(f"\n9. Integration with Alert System:")
    print(f"   ```python")
    print(f"   # In alert_manager.py")
    print(f"   detections = detector.detect(frame)")
    print(f"   humans = detector.get_human_detections(detections)")
    print(f"   ")
    print(f"   for human in humans:")
    print(f"       distance = distance_calc.calculate(human, frame.camera_id)")
    print(f"       if distance < alert_threshold:")
    print(f"           trigger_alert('Person detected near entrance')")
    print(f"   ```")
    
    # Cleanup
    detector.stop()
    print(f"\n✅ Example completed successfully!")
    print(f"\nNext steps:")
    print(f"• Run: python scripts/test_detection.py --webcam")
    print(f"• Or:  python scripts/test_detection.py --image path/to/image.jpg")


if __name__ == "__main__":
    try:
        example_usage()
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print(f"Please install requirements: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)