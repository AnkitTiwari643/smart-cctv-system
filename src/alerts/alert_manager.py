"""Alert manager module - Complete implementation with TTS and rule evaluation."""
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import cv2

from loguru import logger
from utils.audio_utils import TTSEngine
from utils.database import Database


@dataclass
class AlertCondition:
    """Alert rule condition."""
    camera_ids: List[str]
    time_range: Optional[List[str]]  # ["HH:MM", "HH:MM"]
    object_class: str
    distance_to_reference: Optional[Dict[str, Any]]
    zone_name: Optional[str]
    confidence_threshold: float = 0.5


@dataclass
class AlertAction:
    """Alert action to execute."""
    action_type: str  # "audio_alert", "snapshot", "log", "webhook"
    message: Optional[str] = None
    speaker: Optional[str] = None
    severity: str = "info"
    webhook_url: Optional[str] = None


@dataclass
class AlertRule:
    """Complete alert rule definition."""
    name: str
    enabled: bool
    priority: str  # "critical", "high", "medium", "low"
    conditions: AlertCondition
    actions: List[AlertAction]
    cooldown: int = 60  # seconds
    last_triggered: float = 0.0


@dataclass
class AlertEvent:
    """Alert event record."""
    rule_name: str
    timestamp: float
    camera_id: str
    track_id: int
    message: str
    severity: str
    triggered_actions: List[str]


class AlertManager:
    """Main alert management system."""
    
    def __init__(self, config):
        """Initialize alert manager."""
        self.config = config
        self.rules: Dict[str, AlertRule] = {}
        self.recent_alerts: List[AlertEvent] = []
        self.tts_engine = None
        self.database = None
        self.lock = threading.Lock()
        
        # Initialize components
        self._initialize_tts()
        self._load_alert_rules()
        
        # Create snapshots directory
        self.snapshots_dir = Path(config.get("storage.snapshots_dir", "./data/snapshots"))
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Alert manager initialized with {len(self.rules)} rules")
    
    def _initialize_tts(self):
        """Initialize TTS engine."""
        try:
            tts_config = self.config.get("tts", {})
            self.tts_engine = TTSEngine(tts_config)
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    

    
    def _load_alert_rules(self):
        """Load alert rules from configuration."""
        try:
            rules_config = self.config.get("alert_rules", [])
            
            for rule_config in rules_config:
                rule = self._parse_alert_rule(rule_config)
                if rule:
                    self.rules[rule.name] = rule
            
            logger.info(f"Loaded {len(self.rules)} alert rules")
            
        except Exception as e:
            logger.error(f"Failed to load alert rules: {e}")
    
    def _parse_alert_rule(self, rule_config: Dict[str, Any]) -> Optional[AlertRule]:
        """Parse alert rule from configuration."""
        try:
            # Parse conditions
            conditions_config = rule_config.get("conditions", {})
            conditions = AlertCondition(
                camera_ids=conditions_config.get("camera_ids", []),
                time_range=conditions_config.get("time_range"),
                object_class=conditions_config.get("object_class", "person"),
                distance_to_reference=conditions_config.get("distance_to_reference"),
                zone_name=conditions_config.get("zone_name"),
                confidence_threshold=conditions_config.get("confidence_threshold", 0.5)
            )
            
            # Parse actions
            actions = []
            actions_config = rule_config.get("actions", [])
            for action_config in actions_config:
                action = AlertAction(
                    action_type=action_config.get("type"),
                    message=action_config.get("message"),
                    speaker=action_config.get("speaker"),
                    severity=action_config.get("severity", "info"),
                    webhook_url=action_config.get("webhook_url")
                )
                actions.append(action)
            
            # Create rule
            rule = AlertRule(
                name=rule_config.get("name"),
                enabled=rule_config.get("enabled", True),
                priority=rule_config.get("priority", "medium"),
                conditions=conditions,
                actions=actions,
                cooldown=rule_config.get("cooldown", 60)
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"Failed to parse alert rule: {e}")
            return None
    
    def evaluate(self, tracks, frame):
        """
        Evaluate tracks against alert rules.
        
        Args:
            tracks: List of Track objects
            frame: Frame object
        """
        current_time = time.time()
        
        with self.lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                # Check cooldown
                if current_time - rule.last_triggered < rule.cooldown:
                    continue
                
                # Evaluate rule against tracks
                if self._evaluate_rule(rule, tracks, frame):
                    self._trigger_alert(rule, tracks, frame)
                    rule.last_triggered = current_time
    
    def _evaluate_rule(self, rule: AlertRule, tracks, frame) -> bool:
        """
        Evaluate if rule conditions are met.
        
        Args:
            rule: Alert rule to evaluate
            tracks: List of Track objects
            frame: Frame object
            
        Returns:
            True if conditions are met
        """
        try:
            conditions = rule.conditions
            
            # Check camera filter
            if conditions.camera_ids and frame.camera_id not in conditions.camera_ids:
                return False
            
            # Check time range
            if conditions.time_range and not self._is_in_time_range(conditions.time_range):
                return False
            
            # Check for matching tracks
            for track in tracks:
                if self._track_matches_conditions(track, conditions, frame.camera_id):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {e}")
            return False
    
    def _track_matches_conditions(self, track, conditions: AlertCondition, camera_id: str) -> bool:
        """Check if track matches rule conditions."""
        # Check object class
        if track.class_name != conditions.object_class:
            return False
        
        # Check confidence
        if track.confidence < conditions.confidence_threshold:
            return False
        
        # Check distance to reference
        if conditions.distance_to_reference:
            if not self._check_distance_condition(track, conditions.distance_to_reference):
                return False
        
        # Check zone (if implemented in distance calculator)
        if conditions.zone_name:
            # This would require zone checking in distance calculator
            pass
        
        return True
    
    def _check_distance_condition(self, track, distance_condition: Dict[str, Any]) -> bool:
        """Check distance-based condition."""
        try:
            if not hasattr(track, 'distance_info') or not track.distance_info:
                return False
            
            reference = distance_condition.get("reference")
            operator = distance_condition.get("operator", "less_than")
            value = distance_condition.get("value", 0.0)
            
            if not reference:
                return False
            
            # Get distance to reference
            distance_to_ref = track.distance_info.get("distance_to_reference", {})
            if reference not in distance_to_ref:
                return False
            
            distance = distance_to_ref[reference]
            
            # Apply operator
            if operator == "less_than":
                return distance < value
            elif operator == "greater_than":
                return distance > value
            elif operator == "equal":
                return abs(distance - value) < 0.1  # Allow small tolerance
            
            return False
            
        except Exception as e:
            logger.warning(f"Distance condition check error: {e}")
            return False
    
    def _is_in_time_range(self, time_range: List[str]) -> bool:
        """Check if current time is within specified range."""
        try:
            if len(time_range) != 2:
                return True
            
            start_time, end_time = time_range
            current_time = datetime.now().time()
            
            # Parse time strings
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))
            
            start = datetime.now().replace(hour=start_hour, minute=start_min, second=0, microsecond=0).time()
            end = datetime.now().replace(hour=end_hour, minute=end_min, second=0, microsecond=0).time()
            
            # Handle overnight time ranges
            if start <= end:
                return start <= current_time <= end
            else:
                return current_time >= start or current_time <= end
                
        except Exception as e:
            logger.warning(f"Time range check error: {e}")
            return True
    
    def _trigger_alert(self, rule: AlertRule, tracks, frame):
        """
        Trigger alert actions.
        
        Args:
            rule: Alert rule that was triggered
            tracks: List of Track objects
            frame: Frame object
        """
        logger.warning(f"Alert triggered: {rule.name}")
        
        # Find the track that triggered the alert
        trigger_track = None
        for track in tracks:
            if self._track_matches_conditions(track, rule.conditions, frame.camera_id):
                trigger_track = track
                break
        
        if not trigger_track:
            return
        
        # Create alert event
        alert_event = AlertEvent(
            rule_name=rule.name,
            timestamp=time.time(),
            camera_id=frame.camera_id,
            track_id=trigger_track.track_id,
            message=f"Alert: {rule.name} triggered by {trigger_track.class_name}",
            severity=rule.priority,
            triggered_actions=[]
        )
        
        # Execute actions
        for action in rule.actions:
            success = self._execute_action(action, alert_event, trigger_track, frame)
            if success:
                alert_event.triggered_actions.append(action.action_type)
        
        # Store alert
        self.recent_alerts.append(alert_event)
        
        # Keep only recent alerts (last 1000)
        if len(self.recent_alerts) > 1000:
            self.recent_alerts = self.recent_alerts[-1000:]
        
        # Log to database if available
        if self.database:
            self._log_alert_to_database(alert_event)
    
    def _execute_action(self, action: AlertAction, alert_event: AlertEvent, 
                       track, frame) -> bool:
        """
        Execute a specific alert action.
        
        Args:
            action: Alert action to execute
            alert_event: Alert event context
            track: Track that triggered the alert
            frame: Frame object
            
        Returns:
            True if action executed successfully
        """
        try:
            if action.action_type == "audio_alert":
                return self._execute_audio_alert(action, alert_event, track)
            
            elif action.action_type == "snapshot":
                return self._execute_snapshot(action, alert_event, track, frame)
            
            elif action.action_type == "log":
                return self._execute_log(action, alert_event, track)
            
            elif action.action_type == "webhook":
                return self._execute_webhook(action, alert_event, track)
            
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute action {action.action_type}: {e}")
            return False
    
    def _execute_audio_alert(self, action: AlertAction, alert_event: AlertEvent, track) -> bool:
        """Execute audio alert action."""
        if not self.tts_engine or not action.message:
            return False
        
        try:
            # Play audio alert using TTS
            success = self.tts_engine.speak(action.message, blocking=False)
            
            if success:
                logger.info(f"Audio alert played: {action.message}")
            else:
                logger.warning(f"Failed to play audio alert: {action.message}")
            
            return success
            
        except Exception as e:
            logger.error(f"Audio alert error: {e}")
            return False
    
    def _execute_snapshot(self, action: AlertAction, alert_event: AlertEvent, 
                         track, frame) -> bool:
        """Execute snapshot action."""
        try:
            # Create filename
            timestamp = datetime.fromtimestamp(alert_event.timestamp)
            filename = (
                f"{alert_event.camera_id}_{alert_event.rule_name}_"
                f"{timestamp.strftime('%Y%m%d_%H%M%S')}_track{alert_event.track_id}.jpg"
            )
            filepath = self.snapshots_dir / filename
            
            # Draw bounding box on image
            image = frame.image.copy()
            x1, y1, x2, y2 = track.bbox
            
            # Draw detection box
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add label
            label = f"{track.class_name} (ID: {track.track_id})"
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add timestamp
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(image, timestamp_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Save image
            cv2.imwrite(str(filepath), image)
            
            logger.info(f"Snapshot saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Snapshot error: {e}")
            return False
    
    def _execute_log(self, action: AlertAction, alert_event: AlertEvent, track) -> bool:
        """Execute log action."""
        try:
            severity = action.severity.upper()
            message = action.message or alert_event.message
            
            if severity == "CRITICAL":
                logger.critical(message)
            elif severity == "ERROR":
                logger.error(message)
            elif severity == "WARNING":
                logger.warning(message)
            else:
                logger.info(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Log action error: {e}")
            return False
    
    def _execute_webhook(self, action: AlertAction, alert_event: AlertEvent, track) -> bool:
        """Execute webhook action."""
        try:
            if not action.webhook_url:
                return False
            
            import requests
            import json
            
            # Prepare payload
            payload = {
                "alert_rule": alert_event.rule_name,
                "timestamp": alert_event.timestamp,
                "camera_id": alert_event.camera_id,
                "track_id": alert_event.track_id,
                "object_class": track.class_name,
                "confidence": track.confidence,
                "message": alert_event.message,
                "severity": alert_event.severity
            }
            
            # Send webhook
            response = requests.post(
                action.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook sent successfully: {action.webhook_url}")
                return True
            else:
                logger.warning(f"Webhook failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
    
    def _log_alert_to_database(self, alert_event: AlertEvent):
        """Log alert to database."""
        try:
            if not self.database:
                return
            
            alert_data = {
                "timestamp": alert_event.timestamp,
                "alert_type": alert_event.rule_name,
                "message": alert_event.message,
                "severity": alert_event.severity,
                "delivered": 1 if alert_event.triggered_actions else 0
            }
            
            self.database.insert_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Database logging error: {e}")
    
    def set_database(self, database: Database):
        """Set database instance for logging."""
        self.database = database
    
    def get_recent_alerts(self, limit: int = 50) -> List[AlertEvent]:
        """Get recent alert events."""
        with self.lock:
            return self.recent_alerts[-limit:] if self.recent_alerts else []
    
    def get_active_rules(self) -> List[str]:
        """Get list of active rule names."""
        return [name for name, rule in self.rules.items() if rule.enabled]
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable alert rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
            logger.info(f"Alert rule enabled: {rule_name}")
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable alert rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            logger.info(f"Alert rule disabled: {rule_name}")
            return True
        return False
    
    def test_audio_alert(self, message: str) -> bool:
        """Test audio alert functionality."""
        try:
            if not self.tts_engine:
                logger.error("TTS engine not available")
                return False
            
            success = self.tts_engine.speak(message, blocking=False)
            
            if success:
                logger.info(f"Audio test successful: {message}")
            else:
                logger.warning(f"Audio test failed: {message}")
            
            return success
            
        except Exception as e:
            logger.error(f"Audio test error: {e}")
            return False
    
    def stop(self):
        """Stop alert manager and cleanup resources."""
        logger.info("Stopping alert manager")
        
        with self.lock:
            self.rules.clear()
            self.recent_alerts.clear()
        
        if self.tts_engine:
            # TTS engine doesn't need explicit cleanup
            pass
        

