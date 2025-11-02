"""
Simple audio utilities for text-to-speech alerts.
"""
import threading
from typing import Dict, Any, Optional, List

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from loguru import logger


class TTSEngine:
    """Simple Text-to-Speech engine wrapper using pyttsx3."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize TTS engine with basic configuration."""
        self.rate = config.get("rate", 150)
        self.volume = config.get("volume", 0.9)
        self.engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the pyttsx3 engine."""
        try:
            if pyttsx3 is not None:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', self.rate)
                self.engine.setProperty('volume', self.volume)
                logger.info("TTS engine initialized successfully")
            else:
                logger.warning("pyttsx3 not available - audio alerts will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def speak(self, text: str, blocking: bool = False) -> bool:
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            blocking: Whether to wait for speech to complete
            
        Returns:
            True if successful
        """
        try:
            if not self.engine:
                return False
                
            self.engine.say(text)
            if blocking:
                self.engine.runAndWait()
            else:
                # Run in separate thread for non-blocking
                def speak_thread():
                    self.engine.runAndWait()
                threading.Thread(target=speak_thread, daemon=True).start()
            return True
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    



