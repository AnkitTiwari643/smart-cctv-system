"""Object tracker module - DeepSORT-based implementation."""
import time
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from scipy.spatial.distance import euclidean
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter
from loguru import logger


@dataclass
class Track:
    """Track object representing a tracked entity across frames."""
    track_id: int
    class_name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    center_point: tuple  # (x, y)
    area: float
    first_seen: float
    last_seen: float
    hits: int = 0
    hit_streak: int = 0
    time_since_update: int = 0
    is_confirmed: bool = False
    trajectory: List[tuple] = field(default_factory=list)
    velocity: tuple = (0.0, 0.0)
    distance_info: Dict = field(default_factory=dict)
    
    def update_trajectory(self, center_point: tuple):
        """Update trajectory with new center point."""
        self.trajectory.append((center_point, time.time()))
        # Keep only last 100 points
        if len(self.trajectory) > 100:
            self.trajectory = self.trajectory[-100:]
    
    def calculate_velocity(self):
        """Calculate velocity based on recent trajectory points."""
        if len(self.trajectory) < 2:
            self.velocity = (0.0, 0.0)
            return
        
        # Use last two points
        (x1, y1), t1 = self.trajectory[-2]
        (x2, y2), t2 = self.trajectory[-1]
        
        dt = t2 - t1
        if dt > 0:
            vx = (x2 - x1) / dt
            vy = (y2 - y1) / dt
            self.velocity = (vx, vy)
        else:
            self.velocity = (0.0, 0.0)
    
    def get_state_vector(self):
        """Get state vector for Kalman filter."""
        x, y = self.center_point
        return np.array([x, y, self.velocity[0], self.velocity[1]])


class KalmanBoxTracker:
    """Kalman filter-based tracker for individual objects."""
    
    count = 0
    
    def __init__(self, detection, class_name: str):
        """Initialize Kalman tracker with detection."""
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        
        # State transition matrix (constant velocity model)
        self.kf.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=float)
        
        # Measurement function
        self.kf.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)
        
        # Measurement noise
        self.kf.R *= 10.0
        
        # Process noise
        self.kf.Q[2:, 2:] *= 0.01
        
        # Initial state
        x, y = detection.center_point
        self.kf.x = np.array([x, y, 0, 0], dtype=float)
        
        # Initial covariance
        self.kf.P[2:, 2:] *= 1000.0
        self.kf.P *= 10.0
        
        # Track properties
        KalmanBoxTracker.count += 1
        self.id = KalmanBoxTracker.count
        self.class_name = class_name
        self.confidence = detection.confidence
        self.bbox = detection.bbox
        self.area = detection.area
        self.time_since_update = 0
        self.hits = 1
        self.hit_streak = 1
        self.age = 1
        self.history = []
    
    def update(self, detection):
        """Update tracker with new detection."""
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        
        # Update with measurement
        z = np.array([detection.center_point[0], detection.center_point[1]], dtype=float)
        self.kf.update(z)
        
        # Update properties
        self.confidence = detection.confidence
        self.bbox = detection.bbox
        self.area = detection.area
    
    def predict(self):
        """Predict next state."""
        self.kf.predict()
        self.age += 1
        
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        
        # Get predicted center point
        predicted_center = (int(self.kf.x[0]), int(self.kf.x[1]))
        return predicted_center
    
    def get_state(self):
        """Get current state as center point."""
        return (int(self.kf.x[0]), int(self.kf.x[1]))


class ObjectTracker:
    """Main object tracker interface using DeepSORT-like tracking."""
    
    def __init__(self, config):
        """Initialize tracker with configuration."""
        self.config = config
        
        # Tracking parameters
        self.max_age = config.get("processing.tracking.max_age", 30)
        self.min_hits = config.get("processing.tracking.min_hits", 3)
        self.iou_threshold = config.get("processing.tracking.iou_threshold", 0.3)
        
        # Track storage per camera
        self.trackers: Dict[str, List[KalmanBoxTracker]] = defaultdict(list)
        self.frame_count: Dict[str, int] = defaultdict(int)
        
        logger.info(f"Initializing object tracker with max_age={self.max_age}, min_hits={self.min_hits}")
    
    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union (IoU) of two bounding boxes."""
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
    
    def _calculate_distance(self, center1, center2):
        """Calculate Euclidean distance between two center points."""
        return euclidean(center1, center2)
    
    def _associate_detections_to_trackers(self, detections, trackers):
        """Associate detections to existing trackers using Hungarian algorithm."""
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)
        
        # Create cost matrix
        cost_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
        
        for d, detection in enumerate(detections):
            for t, tracker in enumerate(trackers):
                # Use IoU as similarity metric
                predicted_box = self._predict_box_from_center(tracker.get_state(), detection.bbox)
                iou = self._calculate_iou(detection.bbox, predicted_box)
                cost_matrix[d, t] = 1.0 - iou  # Convert to cost
        
        # Solve assignment problem
        if cost_matrix.size > 0:
            det_indices, trk_indices = linear_sum_assignment(cost_matrix)
            
            # Filter out assignments with low IoU
            matches = []
            for d, t in zip(det_indices, trk_indices):
                if cost_matrix[d, t] < (1.0 - self.iou_threshold):
                    matches.append([d, t])
            
            matches = np.array(matches)
            
            # Get unmatched detections and trackers
            unmatched_detections = []
            for d in range(len(detections)):
                if d not in matches[:, 0] if len(matches) > 0 else True:
                    unmatched_detections.append(d)
            
            unmatched_trackers = []
            for t in range(len(trackers)):
                if t not in matches[:, 1] if len(matches) > 0 else True:
                    unmatched_trackers.append(t)
            
        else:
            matches = np.empty((0, 2), dtype=int)
            unmatched_detections = list(range(len(detections)))
            unmatched_trackers = list(range(len(trackers)))
        
        return matches, np.array(unmatched_detections), np.array(unmatched_trackers)
    
    def _predict_box_from_center(self, center, reference_box):
        """Predict bounding box from center point using reference box size."""
        x, y = center
        ref_x1, ref_y1, ref_x2, ref_y2 = reference_box
        w = ref_x2 - ref_x1
        h = ref_y2 - ref_y1
        
        return (
            int(x - w/2),
            int(y - h/2),
            int(x + w/2),
            int(y + h/2)
        )
    
    def update(self, detections, camera_id):
        """
        Update tracker with new detections.
        
        Args:
            detections: List of Detection objects
            camera_id: Camera identifier
            
        Returns:
            List of Track objects
        """
        self.frame_count[camera_id] += 1
        current_time = time.time()
        
        # Get existing trackers for this camera
        trackers = self.trackers[camera_id]
        
        # Predict next state for all trackers
        for tracker in trackers:
            tracker.predict()
        
        # Associate detections to trackers
        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(
            detections, trackers
        )
        
        # Update matched trackers
        for det_idx, trk_idx in matched:
            trackers[trk_idx].update(detections[det_idx])
        
        # Create new trackers for unmatched detections
        for det_idx in unmatched_dets:
            detection = detections[det_idx]
            new_tracker = KalmanBoxTracker(detection, detection.class_name)
            trackers.append(new_tracker)
        
        # Remove dead trackers
        active_trackers = []
        for tracker in trackers:
            if tracker.time_since_update <= self.max_age:
                active_trackers.append(tracker)
        
        self.trackers[camera_id] = active_trackers
        
        # Convert to Track objects
        tracks = []
        for tracker in active_trackers:
            # Only return confirmed tracks
            if tracker.hits >= self.min_hits or tracker.hit_streak >= 1:
                track = Track(
                    track_id=tracker.id,
                    class_name=tracker.class_name,
                    confidence=tracker.confidence,
                    bbox=tracker.bbox,
                    center_point=tracker.get_state(),
                    area=tracker.area,
                    first_seen=current_time - (tracker.age * 0.1),  # Approximate
                    last_seen=current_time,
                    hits=tracker.hits,
                    hit_streak=tracker.hit_streak,
                    time_since_update=tracker.time_since_update,
                    is_confirmed=tracker.hits >= self.min_hits
                )
                
                # Update trajectory
                track.update_trajectory(track.center_point)
                track.calculate_velocity()
                
                tracks.append(track)
        
        logger.debug(f"Tracking update for {camera_id}: {len(detections)} detections -> {len(tracks)} tracks")
        
        return tracks
    
    def get_track_by_id(self, track_id: int, camera_id: str) -> Optional[Track]:
        """Get specific track by ID and camera."""
        trackers = self.trackers[camera_id]
        for tracker in trackers:
            if tracker.id == track_id:
                track = Track(
                    track_id=tracker.id,
                    class_name=tracker.class_name,
                    confidence=tracker.confidence,
                    bbox=tracker.bbox,
                    center_point=tracker.get_state(),
                    area=tracker.area,
                    first_seen=time.time() - (tracker.age * 0.1),
                    last_seen=time.time(),
                    hits=tracker.hits,
                    hit_streak=tracker.hit_streak,
                    time_since_update=tracker.time_since_update,
                    is_confirmed=tracker.hits >= self.min_hits
                )
                return track
        return None
    
    def get_active_tracks_count(self, camera_id: str) -> int:
        """Get count of active tracks for camera."""
        return len([t for t in self.trackers[camera_id] if t.hits >= self.min_hits])
    
    def stop(self):
        """Stop tracker and cleanup resources."""
        logger.info("Stopping object tracker")
        self.trackers.clear()
        self.frame_count.clear()
