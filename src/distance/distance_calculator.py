"""Distance calculator module - Calibration-based implementation."""
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class ReferencePoint:
    """Reference point for distance calculation."""
    name: str
    position: Tuple[int, int]  # (x, y) pixel coordinates
    real_distance: float  # meters from camera
    world_coordinates: Optional[Tuple[float, float, float]] = None  # (x, y, z) in meters


@dataclass
class DistanceInfo:
    """Distance measurement result."""
    distance_to_camera: float
    distance_to_references: Dict[str, float]
    estimated_world_coordinates: Optional[Tuple[float, float, float]]
    confidence: float


class CameraCalibration:
    """Camera calibration data for distance calculation."""
    
    def __init__(self, camera_config: Dict[str, Any]):
        """
        Initialize camera calibration.
        
        Args:
            camera_config: Camera configuration from config file
        """
        self.camera_id = camera_config.get('id')
        self.reference_points = []
        
        # Load reference points
        ref_points = camera_config.get('reference_points', [])
        for ref in ref_points:
            point = ReferencePoint(
                name=ref['name'],
                position=tuple(ref['position']),
                real_distance=ref['real_distance']
            )
            self.reference_points.append(point)
        
        # Camera parameters (can be expanded for more sophisticated calibration)
        self.focal_length = None
        self.sensor_height = None
        self.image_height = None
        
        # Calculate calibration if we have enough reference points
        if len(self.reference_points) >= 1:
            self._calculate_calibration()
        
        logger.info(f"Camera calibration for {self.camera_id}: {len(self.reference_points)} reference points")
    
    def _calculate_calibration(self):
        """Calculate camera calibration parameters from reference points."""
        # Simple calibration using the first reference point
        # In a more sophisticated implementation, we would use multiple points
        # and solve for intrinsic camera parameters
        
        if not self.reference_points:
            return
        
        ref_point = self.reference_points[0]
        
        # Assume standard camera parameters if not specified
        # These would ideally come from camera calibration
        self.image_height = 1080  # Standard height, should come from actual image
        self.sensor_height = 5.76e-3  # Standard sensor size in meters (can vary)
        
        # Calculate focal length using the reference point
        # Using similar triangles: focal_length / sensor_height = distance / real_world_height
        # We estimate real world height of the object at the reference point
        pixel_y = ref_point.position[1]
        distance_to_ref = ref_point.real_distance
        
        # Assume the reference point is at ground level and camera is mounted at ~2.5m height
        camera_height = 2.5  # meters
        
        # Calculate focal length in pixels
        self.focal_length = (pixel_y * distance_to_ref) / camera_height
        
        logger.debug(f"Calculated focal length: {self.focal_length:.2f} pixels")
    
    def calculate_distance_to_camera(self, object_position: Tuple[int, int], 
                                   object_height_pixels: int) -> float:
        """
        Calculate distance from object to camera using perspective geometry.
        
        Args:
            object_position: (x, y) pixel coordinates of object center
            object_height_pixels: Height of object in pixels
            
        Returns:
            Distance in meters
        """
        if not self.focal_length or not self.reference_points:
            return 0.0
        
        try:
            # Use similar triangles to calculate distance
            # distance = (real_height * focal_length) / pixel_height
            
            # Estimate real height based on object type (this is a simplification)
            # In practice, this would be more sophisticated
            estimated_real_height = 1.7  # Average human height in meters
            
            if object_height_pixels <= 0:
                return 0.0
            
            distance = (estimated_real_height * self.focal_length) / object_height_pixels
            
            # Clamp to reasonable bounds
            distance = max(0.5, min(distance, 100.0))
            
            return distance
            
        except Exception as e:
            logger.warning(f"Error calculating distance: {e}")
            return 0.0
    
    def calculate_distance_to_reference(self, object_position: Tuple[int, int], 
                                      reference_name: str) -> float:
        """
        Calculate distance from object to a reference point.
        
        Args:
            object_position: (x, y) pixel coordinates of object
            reference_name: Name of reference point
            
        Returns:
            Distance in meters
        """
        ref_point = self.get_reference_point(reference_name)
        if not ref_point:
            return float('inf')
        
        try:
            # Calculate pixel distance
            pixel_distance = math.sqrt(
                (object_position[0] - ref_point.position[0]) ** 2 +
                (object_position[1] - ref_point.position[1]) ** 2
            )
            
            # Convert pixel distance to real distance
            # This is a simplified approach using the reference point's known distance
            # More sophisticated methods would use proper camera calibration
            
            if pixel_distance == 0:
                return 0.0
            
            # Use proportional scaling based on the reference point
            # This assumes the reference point and object are roughly at the same depth
            real_distance = (pixel_distance * ref_point.real_distance) / 1000.0  # Rough conversion
            
            return real_distance
            
        except Exception as e:
            logger.warning(f"Error calculating distance to reference {reference_name}: {e}")
            return float('inf')
    
    def get_reference_point(self, name: str) -> Optional[ReferencePoint]:
        """Get reference point by name."""
        for ref in self.reference_points:
            if ref.name == name:
                return ref
        return None


class DistanceCalculator:
    """Distance calculation interface."""
    
    def __init__(self, config):
        """Initialize distance calculator."""
        self.config = config
        self.method = config.get("processing.distance.method", "calibration")
        self.unit = config.get("processing.distance.unit", "meters")
        self.max_distance = config.get("processing.distance.max_distance", 50.0)
        
        # Camera calibrations
        self.calibrations: Dict[str, CameraCalibration] = {}
        
        # Load camera calibrations
        cameras = config.get("cameras", [])
        for camera_config in cameras:
            camera_id = camera_config.get('id')
            if camera_id:
                self.calibrations[camera_id] = CameraCalibration(camera_config)
        
        logger.info(f"Distance calculator initialized with method: {self.method}")
        logger.info(f"Loaded calibrations for {len(self.calibrations)} cameras")
    
    def calculate(self, track, camera_id: str) -> Dict[str, Any]:
        """
        Calculate distance for tracked object.
        
        Args:
            track: Track object with position and bbox information
            camera_id: Camera identifier
            
        Returns:
            Distance measurement dictionary
        """
        calibration = self.calibrations.get(camera_id)
        if not calibration:
            logger.warning(f"No calibration found for camera {camera_id}")
            return {
                "distance_to_camera": 0.0,
                "distance_to_reference": {},
                "confidence": 0.0
            }
        
        try:
            # Calculate object height in pixels
            x1, y1, x2, y2 = track.bbox
            object_height = y2 - y1
            
            # Calculate distance to camera
            distance_to_camera = calibration.calculate_distance_to_camera(
                track.center_point, object_height
            )
            
            # Calculate distances to all reference points
            distance_to_references = {}
            for ref_point in calibration.reference_points:
                distance = calibration.calculate_distance_to_reference(
                    track.center_point, ref_point.name
                )
                distance_to_references[ref_point.name] = distance
            
            # Calculate confidence based on object size and position
            confidence = self._calculate_confidence(track, calibration)
            
            result = {
                "distance_to_camera": distance_to_camera,
                "distance_to_reference": distance_to_references,
                "confidence": confidence,
                "method": self.method,
                "unit": self.unit
            }
            
            logger.debug(f"Distance calculated for track {track.track_id}: {distance_to_camera:.2f}m")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating distance for track {track.track_id}: {e}")
            return {
                "distance_to_camera": 0.0,
                "distance_to_reference": {},
                "confidence": 0.0
            }
    
    def _calculate_confidence(self, track, calibration: CameraCalibration) -> float:
        """
        Calculate confidence score for distance measurement.
        
        Args:
            track: Track object
            calibration: Camera calibration
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 1.0
        
        # Reduce confidence based on object size (very small or very large objects are less reliable)
        object_area = track.area
        if object_area < 1000:  # Very small object
            confidence *= 0.5
        elif object_area > 50000:  # Very large object
            confidence *= 0.7
        
        # Reduce confidence based on position (objects at edges are less reliable)
        x, y = track.center_point
        # Assume image dimensions (should come from actual image)
        image_width, image_height = 1920, 1080
        
        edge_margin = 0.1  # 10% margin
        if (x < image_width * edge_margin or x > image_width * (1 - edge_margin) or
            y < image_height * edge_margin or y > image_height * (1 - edge_margin)):
            confidence *= 0.8
        
        # Reduce confidence based on detection confidence
        confidence *= track.confidence
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def get_nearby_objects(self, tracks: List, reference_name: str, 
                          max_distance: float, camera_id: str) -> List:
        """
        Get objects within specified distance of a reference point.
        
        Args:
            tracks: List of Track objects
            reference_name: Name of reference point
            max_distance: Maximum distance threshold
            camera_id: Camera identifier
            
        Returns:
            List of tracks within distance threshold
        """
        nearby_tracks = []
        
        for track in tracks:
            if not hasattr(track, 'distance_info') or not track.distance_info:
                continue
            
            distance_to_ref = track.distance_info.get('distance_to_reference', {})
            if reference_name in distance_to_ref:
                distance = distance_to_ref[reference_name]
                if distance <= max_distance:
                    nearby_tracks.append(track)
        
        return nearby_tracks
    
    def is_object_in_zone(self, track, zone_config: Dict, camera_id: str) -> bool:
        """
        Check if object is within a defined zone.
        
        Args:
            track: Track object
            zone_config: Zone configuration with polygon definition
            camera_id: Camera identifier
            
        Returns:
            True if object is in zone
        """
        try:
            # Get zone polygon
            polygon_points = zone_config.get('polygon', [])
            if len(polygon_points) < 3:
                return False
            
            # Check if track center point is inside polygon
            x, y = track.center_point
            return self._point_in_polygon(x, y, polygon_points)
            
        except Exception as e:
            logger.warning(f"Error checking zone containment: {e}")
            return False
    
    def _point_in_polygon(self, x: int, y: int, polygon: List[List[int]]) -> bool:
        """
        Check if point is inside polygon using ray casting algorithm.
        
        Args:
            x, y: Point coordinates
            polygon: List of [x, y] polygon vertices
            
        Returns:
            True if point is inside polygon
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def stop(self):
        """Stop calculator and cleanup resources."""
        logger.info("Stopping distance calculator")
        self.calibrations.clear()
