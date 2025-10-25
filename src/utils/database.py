"""
Database abstraction layer for event and alert storage.
"""
import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class Database:
    """SQLite database interface for the Smart CCTV System."""
    
    def __init__(self, db_path: str = "data/events.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self.cursor = None
        
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # Events table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    camera_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    track_id INTEGER,
                    class_name TEXT,
                    distance REAL,
                    alert_triggered INTEGER DEFAULT 0,
                    snapshot_path TEXT,
                    metadata TEXT
                )
            """)
            
            # Alerts table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_id INTEGER,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    delivered INTEGER DEFAULT 0,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)
            
            # Tracks table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    track_id INTEGER PRIMARY KEY,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    camera_id TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    trajectory TEXT
                )
            """)
            
            # Create indexes
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_camera 
                ON events(camera_id)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                ON alerts(timestamp)
            """)
            
            self.conn.commit()
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def insert_event(self, event_data: Dict[str, Any]) -> int:
        """
        Insert detection event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Event ID
        """
        try:
            metadata = event_data.get('metadata', {})
            
            self.cursor.execute("""
                INSERT INTO events (
                    timestamp, camera_id, event_type, track_id,
                    class_name, distance, alert_triggered, snapshot_path, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data['timestamp'],
                event_data['camera_id'],
                event_data['event_type'],
                event_data.get('track_id'),
                event_data.get('class_name'),
                event_data.get('distance'),
                event_data.get('alert_triggered', 0),
                event_data.get('snapshot_path'),
                json.dumps(metadata)
            ))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to insert event: {e}")
            return -1
    
    def insert_alert(self, alert_data: Dict[str, Any]) -> int:
        """
        Insert alert record.
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            Alert ID
        """
        try:
            self.cursor.execute("""
                INSERT INTO alerts (
                    timestamp, event_id, alert_type, message, severity, delivered
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert_data['timestamp'],
                alert_data.get('event_id'),
                alert_data['alert_type'],
                alert_data['message'],
                alert_data['severity'],
                alert_data.get('delivered', 0)
            ))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to insert alert: {e}")
            return -1
    
    def get_recent_events(self, limit: int = 100, camera_id: Optional[str] = None) -> List[Dict]:
        """
        Get recent events.
        
        Args:
            limit: Maximum number of events to return
            camera_id: Filter by camera ID (optional)
            
        Returns:
            List of event dictionaries
        """
        try:
            query = "SELECT * FROM events"
            params = []
            
            if camera_id:
                query += " WHERE camera_id = ?"
                params.append(camera_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """
        Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert dictionaries
        """
        try:
            self.cursor.execute("""
                SELECT * FROM alerts
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def cleanup_old_data(self, retention_days: int = 30):
        """
        Delete old events and alerts.
        
        Args:
            retention_days: Number of days to keep
        """
        try:
            cutoff = time.time() - (retention_days * 86400)
            
            # Delete old events
            self.cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))
            events_deleted = self.cursor.rowcount
            
            # Delete old alerts
            self.cursor.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff,))
            alerts_deleted = self.cursor.rowcount
            
            self.conn.commit()
            
            logger.info(f"Cleaned up old data: {events_deleted} events, {alerts_deleted} alerts deleted")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = {}
            
            # Total events
            self.cursor.execute("SELECT COUNT(*) FROM events")
            stats['total_events'] = self.cursor.fetchone()[0]
            
            # Total alerts
            self.cursor.execute("SELECT COUNT(*) FROM alerts")
            stats['total_alerts'] = self.cursor.fetchone()[0]
            
            # Events today
            today_start = time.time() - 86400
            self.cursor.execute("SELECT COUNT(*) FROM events WHERE timestamp > ?", (today_start,))
            stats['events_today'] = self.cursor.fetchone()[0]
            
            # Alerts today
            self.cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp > ?", (today_start,))
            stats['alerts_today'] = self.cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
