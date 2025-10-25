#!/usr/bin/env python3
"""
Test script for object detection functionality.
"""
import sys
import os
import cv2
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from detection.object_detector import ObjectDetector
from utils.config_loader import ConfigLoader


class MockFrame:
    """Mock frame for testing."""
    def __init__(self, image, camera_id="test"):
        self.image = image
        self.camera_id = camera_id
        self.timestamp = time.time()


def test_detection_on_image(image_path: str, config_path: str = "config/config.yaml"):
    """Test object detection on a single image."""
    
    print(f"Testing object detection on: {image_path}")
    
    # Load configuration
    try:
        config = ConfigLoader(config_path)
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    # Initialize detector
    try:
        detector = ObjectDetector(config)
        print("✓ Object detector initialized")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        return False
    
    # Load test image
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"✗ Could not load image: {image_path}")
            return False
        print(f"✓ Image loaded: {image.shape}")
    except Exception as e:
        print(f"✗ Error loading image: {e}")
        return False
    
    # Create mock frame
    frame = MockFrame(image, "test_camera")
    
    # Run detection
    try:
        start_time = time.time()
        detections = detector.detect(frame)
        detection_time = time.time() - start_time
        
        print(f"✓ Detection completed in {detection_time:.3f}s")
        print(f"✓ Found {len(detections)} objects")
        
        # Print detection details
        for i, detection in enumerate(detections):
            print(f"  {i+1}. {detection.class_name} (conf: {detection.confidence:.3f}) "
                  f"at {detection.bbox}")
        
        # Draw detections and save result
        if detections:
            annotated_image = detector.detect_and_draw(frame)
            output_path = f"test_detection_result_{int(time.time())}.jpg"
            cv2.imwrite(output_path, annotated_image)
            print(f"✓ Annotated image saved: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Detection failed: {e}")
        return False
    
    finally:
        detector.stop()


def test_detection_on_webcam(config_path: str = "config/config.yaml", duration: int = 30):
    """Test object detection on webcam feed."""
    
    print(f"Testing object detection on webcam for {duration} seconds...")
    
    # Load configuration
    config = ConfigLoader(config_path)
    detector = ObjectDetector(config)
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("✗ Could not open webcam")
        return False
    
    print("✓ Webcam opened - Press 'q' to quit")
    
    start_time = time.time()
    frame_count = 0
    
    try:
        while time.time() - start_time < duration:
            ret, image = cap.read()
            if not ret:
                break
            
            frame = MockFrame(image, "webcam")
            
            # Run detection
            detections = detector.detect(frame)
            
            # Draw results
            annotated_image = detector.detect_and_draw(frame)
            
            # Display
            cv2.imshow('Object Detection Test', annotated_image)
            
            # Show detection count
            if frame_count % 30 == 0:  # Every 30 frames
                print(f"Frame {frame_count}: {len(detections)} objects detected")
            
            frame_count += 1
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        print(f"✓ Processed {frame_count} frames in {elapsed:.1f}s (avg FPS: {fps:.1f})")
        
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.stop()
    
    return True


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test object detection")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--image", help="Test on single image")
    parser.add_argument("--webcam", action="store_true", help="Test on webcam")
    parser.add_argument("--duration", type=int, default=30, help="Webcam test duration")
    
    args = parser.parse_args()
    
    if args.image:
        success = test_detection_on_image(args.image, args.config)
    elif args.webcam:
        success = test_detection_on_webcam(args.config, args.duration)
    else:
        print("Please specify --image or --webcam")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())