"""
Audio utilities for speaker management and TTS.
"""
import os
import sys
import time
import threading
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess
import platform

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None

try:
    import pyaudio
except ImportError:
    pyaudio = None

from loguru import logger


class TTSEngine:
    """Text-to-Speech engine wrapper."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TTS engine.
        
        Args:
            config: TTS configuration
        """
        self.engine_type = config.get("engine", "pyttsx3")
        self.rate = config.get("rate", 150)
        self.volume = config.get("volume", 0.9)
        self.voice = config.get("voice", "default")
        self.cache_enabled = config.get("cache_enabled", True)
        self.cache_dir = Path(config.get("cache_dir", "./data/tts_cache"))
        
        self.engine = None
        self.lock = threading.Lock()
        
        # Create cache directory
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the TTS engine."""
        try:
            if self.engine_type == "pyttsx3":
                self.engine = pyttsx3.init()
                
                # Set properties
                self.engine.setProperty('rate', self.rate)
                self.engine.setProperty('volume', self.volume)
                
                # Set voice if specified
                if self.voice != "default":
                    voices = self.engine.getProperty('voices')
                    for voice in voices:
                        if self.voice.lower() in voice.name.lower():
                            self.engine.setProperty('voice', voice.id)
                            break
                
                logger.info(f"TTS engine initialized: {self.engine_type}")
                
            else:
                logger.warning("pyttsx3 not available, using system TTS")
                self.engine_type = "system"
                
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine_type = "system"
    
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
            with self.lock:
                # Check cache first
                if self.cache_enabled:
                    cached_file = self._get_cached_audio(text)
                    if cached_file and cached_file.exists():
                        return self._play_audio_file(str(cached_file))
                
                if self.engine and self.engine_type == "pyttsx3":
                    self.engine.say(text)
                    if blocking:
                        self.engine.runAndWait()
                    else:
                        # Run in separate thread for non-blocking
                        def speak_thread():
                            self.engine.runAndWait()
                        threading.Thread(target=speak_thread, daemon=True).start()
                    
                    # Cache the audio if enabled
                    if self.cache_enabled:
                        self._cache_audio(text)
                    
                    return True
                else:
                    # Fallback to system TTS
                    return self._system_tts(text, blocking)
                    
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    def _get_cached_audio(self, text: str) -> Optional[Path]:
        """Get cached audio file path for text."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.wav"
    
    def _cache_audio(self, text: str):
        """Cache audio for text."""
        try:
            cached_file = self._get_cached_audio(text)
            if not cached_file.exists() and self.engine:
                # Save to file using pyttsx3
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_file.close()
                
                self.engine.save_to_file(text, temp_file.name)
                self.engine.runAndWait()
                
                # Move to cache location
                if os.path.exists(temp_file.name):
                    os.rename(temp_file.name, str(cached_file))
                    logger.debug(f"Cached TTS audio: {cached_file}")
                    
        except Exception as e:
            logger.warning(f"Failed to cache TTS audio: {e}")
    
    def _play_audio_file(self, file_path: str) -> bool:
        """Play audio file."""
        try:
            if pygame:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                return True
            else:
                # Fallback to system player
                return self._system_play(file_path)
                
        except Exception as e:
            logger.error(f"Failed to play audio file: {e}")
            return False
    
    def _system_tts(self, text: str, blocking: bool = False) -> bool:
        """Use system TTS as fallback."""
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                cmd = ["say", text]
            elif system == "windows":
                # Use PowerShell for Windows TTS
                cmd = [
                    "powershell", "-Command",
                    f"Add-Type -AssemblyName System.Speech; "
                    f"$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$speak.Speak('{text}')"
                ]
            else:  # Linux
                # Try espeak or festival
                if subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
                    cmd = ["espeak", text]
                elif subprocess.run(["which", "festival"], capture_output=True).returncode == 0:
                    cmd = ["festival", "--tts"]
                else:
                    logger.warning("No system TTS available")
                    return False
            
            if blocking:
                subprocess.run(cmd, check=True)
            else:
                subprocess.Popen(cmd)
            
            return True
            
        except Exception as e:
            logger.error(f"System TTS error: {e}")
            return False
    
    def _system_play(self, file_path: str) -> bool:
        """Play audio file using system player."""
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                cmd = ["afplay", file_path]
            elif system == "windows":
                cmd = ["start", "", file_path]
            else:  # Linux
                # Try common audio players
                for player in ["aplay", "paplay", "play"]:
                    if subprocess.run(["which", player], capture_output=True).returncode == 0:
                        cmd = [player, file_path]
                        break
                else:
                    return False
            
            subprocess.Popen(cmd)
            return True
            
        except Exception as e:
            logger.error(f"System audio play error: {e}")
            return False


class SpeakerManager:
    """Manages wired and Bluetooth speakers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize speaker manager.
        
        Args:
            config: Speaker configuration
        """
        self.speakers = {}
        self.active_speakers = []
        
        # Load speaker configurations
        speakers_config = config.get("speakers", [])
        for speaker_config in speakers_config:
            speaker = self._create_speaker(speaker_config)
            if speaker:
                self.speakers[speaker.name] = speaker
        
        logger.info(f"Speaker manager initialized with {len(self.speakers)} speakers")
    
    def _create_speaker(self, config: Dict[str, Any]) -> Optional['Speaker']:
        """Create speaker object from configuration."""
        try:
            speaker_type = config.get("type", "wired")
            name = config.get("name", "default")
            enabled = config.get("enabled", True)
            
            if not enabled:
                return None
            
            if speaker_type == "wired":
                return WiredSpeaker(name, config)
            elif speaker_type == "bluetooth":
                return BluetoothSpeaker(name, config)
            elif speaker_type == "group":
                return SpeakerGroup(name, config, self)
            else:
                logger.warning(f"Unknown speaker type: {speaker_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create speaker: {e}")
            return None
    
    def get_speaker(self, name: str) -> Optional['Speaker']:
        """Get speaker by name."""
        return self.speakers.get(name)
    
    def get_available_speakers(self) -> List[str]:
        """Get list of available speaker names."""
        available = []
        for speaker in self.speakers.values():
            if speaker.is_available():
                available.append(speaker.name)
        return available
    
    def play_audio(self, text: str, speaker_names: List[str] = None) -> bool:
        """
        Play audio on specified speakers.
        
        Args:
            text: Text to speak
            speaker_names: List of speaker names (None for all)
            
        Returns:
            True if at least one speaker played successfully
        """
        if speaker_names is None:
            speaker_names = list(self.speakers.keys())
        
        success_count = 0
        for name in speaker_names:
            speaker = self.speakers.get(name)
            if speaker and speaker.is_available():
                if speaker.play(text):
                    success_count += 1
        
        return success_count > 0


class Speaker:
    """Base speaker class."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize speaker."""
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
    
    def is_available(self) -> bool:
        """Check if speaker is available."""
        return self.enabled
    
    def play(self, text: str) -> bool:
        """Play text on speaker."""
        raise NotImplementedError


class WiredSpeaker(Speaker):
    """Wired speaker implementation."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize wired speaker."""
        super().__init__(name, config)
        self.device_id = config.get("device_id", 0)
        self.tts_engine = None
    
    def is_available(self) -> bool:
        """Check if wired speaker is available."""
        if not self.enabled:
            return False
        
        # Check if audio device is available
        if pyaudio:
            try:
                p = pyaudio.PyAudio()
                device_count = p.get_device_count()
                available = self.device_id < device_count
                p.terminate()
                return available
            except:
                return False
        
        return True  # Assume available if can't check
    
    def play(self, text: str) -> bool:
        """Play text on wired speaker."""
        try:
            if not self.tts_engine:
                # Create TTS engine for this speaker
                tts_config = {
                    "engine": "pyttsx3",
                    "rate": 150,
                    "volume": 0.9,
                    "cache_enabled": True,
                    "cache_dir": "./data/tts_cache"
                }
                self.tts_engine = TTSEngine(tts_config)
            
            return self.tts_engine.speak(text, blocking=False)
            
        except Exception as e:
            logger.error(f"Wired speaker {self.name} error: {e}")
            return False


class BluetoothSpeaker(Speaker):
    """Bluetooth speaker implementation."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize Bluetooth speaker."""
        super().__init__(name, config)
        self.mac_address = config.get("mac_address")
        self.is_connected = False
        self.tts_engine = None
    
    def is_available(self) -> bool:
        """Check if Bluetooth speaker is available."""
        if not self.enabled or not self.mac_address:
            return False
        
        # Check Bluetooth connectivity
        return self._check_bluetooth_connection()
    
    def _check_bluetooth_connection(self) -> bool:
        """Check if Bluetooth device is connected."""
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Use system_profiler to check Bluetooth devices
                result = subprocess.run(
                    ["system_profiler", "SPBluetoothDataType"],
                    capture_output=True, text=True
                )
                return self.mac_address.upper() in result.stdout.upper()
                
            elif system == "linux":
                # Use bluetoothctl to check connected devices
                result = subprocess.run(
                    ["bluetoothctl", "info", self.mac_address],
                    capture_output=True, text=True
                )
                return "Connected: yes" in result.stdout
                
            else:  # Windows
                # Basic check - assume connected if configured
                return True
                
        except Exception as e:
            logger.warning(f"Bluetooth check error: {e}")
            return False
    
    def play(self, text: str) -> bool:
        """Play text on Bluetooth speaker."""
        try:
            if not self.is_available():
                logger.warning(f"Bluetooth speaker {self.name} not available")
                return False
            
            if not self.tts_engine:
                # Create TTS engine for this speaker
                tts_config = {
                    "engine": "pyttsx3",
                    "rate": 150,
                    "volume": 0.9,
                    "cache_enabled": True,
                    "cache_dir": "./data/tts_cache"
                }
                self.tts_engine = TTSEngine(tts_config)
            
            return self.tts_engine.speak(text, blocking=False)
            
        except Exception as e:
            logger.error(f"Bluetooth speaker {self.name} error: {e}")
            return False


class SpeakerGroup(Speaker):
    """Group of speakers that can be controlled together."""
    
    def __init__(self, name: str, config: Dict[str, Any], speaker_manager):
        """Initialize speaker group."""
        super().__init__(name, config)
        self.speaker_names = config.get("speakers", [])
        self.speaker_manager = speaker_manager
    
    def is_available(self) -> bool:
        """Check if any speaker in group is available."""
        if not self.enabled:
            return False
        
        for speaker_name in self.speaker_names:
            speaker = self.speaker_manager.speakers.get(speaker_name)
            if speaker and speaker.is_available():
                return True
        return False
    
    def play(self, text: str) -> bool:
        """Play text on all available speakers in group."""
        success_count = 0
        
        for speaker_name in self.speaker_names:
            speaker = self.speaker_manager.speakers.get(speaker_name)
            if speaker and speaker.is_available():
                if speaker.play(text):
                    success_count += 1
        
        return success_count > 0