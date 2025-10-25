# Alert System Design and Implementation

## 1. Alert System Overview

The alert system is the final output stage that delivers real-time notifications to users through audio speakers when specific conditions are met.

### Components
```
Detection Events → Rule Engine → Alert Queue → TTS Engine → Speaker Output
```

---

## 2. Alert Rule Engine

### 2.1 Rule Structure

**Complete rule example**:
```yaml
alert_rules:
  - name: "Night Intruder Detection"
    enabled: true
    priority: "critical"  # critical, high, medium, low
    conditions:
      camera_ids: ["camera_1", "camera_2"]
      time_range: ["22:00", "06:00"]
      days_of_week: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
      object_class: "person"
      confidence_min: 0.7
      distance_to_reference:
        reference: "front_door"
        operator: "less_than"  # less_than, greater_than, between
        value: 5.0
      duration_min: 3  # Object must be present for 3 seconds
    actions:
      - type: "audio_alert"
        message: "Warning! Person detected near entrance at night."
        speaker: "all"
        repeat: 1
      - type: "snapshot"
        save_path: "data/snapshots/alerts/"
      - type: "log"
        severity: "critical"
      - type: "email"  # Optional
        subject: "Security Alert"
        body: "Person detected at {time} near {location}"
    cooldown: 60  # Seconds before same rule can trigger again
    max_alerts_per_hour: 10  # Prevent spam
```

### 2.2 Condition Types

**Time-based conditions**:
```yaml
time_range: ["18:00", "06:00"]  # 6 PM to 6 AM
days_of_week: ["saturday", "sunday"]  # Weekends only
```

**Object-based conditions**:
```yaml
object_class: "person"  # person, car, truck, dog, cat, etc.
confidence_min: 0.6     # Minimum confidence score
object_count:           # Multiple objects
  min: 2
  max: 5
```

**Distance-based conditions**:
```yaml
distance_to_reference:
  reference: "front_door"
  operator: "less_than"
  value: 3.0  # meters

# Or between two values
distance_to_reference:
  reference: "driveway"
  operator: "between"
  value: [2.0, 10.0]
```

**Spatial conditions**:
```yaml
in_zone: "entrance_zone"  # Object must be in defined zone
crossed_line: "perimeter_line"  # Object crossed virtual line
```

**Temporal conditions**:
```yaml
duration_min: 5      # Must be present for 5+ seconds
duration_max: 60     # Alert if loitering more than 60 seconds
velocity_max: 2.0    # Moving slowly (suspicious)
```

**Sequence conditions** (advanced):
```yaml
sequence:
  - step: 1
    object_class: "person"
    action: "enters"
    zone: "driveway"
  - step: 2
    object_class: "person"
    action: "stays"
    zone: "front_door"
    duration: 10
  - step: 3
    object_class: "person"
    action: "leaves"
```

### 2.3 Alert Priorities

**Priority levels**:
- **CRITICAL**: Immediate threat (intruder at night)
- **HIGH**: Important event (person near vehicle)
- **MEDIUM**: Notable event (delivery, visitor)
- **LOW**: Informational (animal detected)

**Priority-based behavior**:
```python
priority_settings = {
    'critical': {
        'volume': 1.0,
        'repeat': 2,
        'interrupt': True,  # Interrupt other alerts
        'rate': 160  # Words per minute (faster)
    },
    'high': {
        'volume': 0.9,
        'repeat': 1,
        'interrupt': False,
        'rate': 150
    },
    'medium': {
        'volume': 0.7,
        'repeat': 1,
        'interrupt': False,
        'rate': 140
    },
    'low': {
        'volume': 0.5,
        'repeat': 1,
        'interrupt': False,
        'rate': 130
    }
}
```

---

## 3. Text-to-Speech Implementation

### 3.1 TTS Engine Selection

**Option 1: pyttsx3 (Offline, Fast)**
```python
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed
engine.setProperty('volume', 0.9)  # Volume

# Get available voices
voices = engine.getProperty('voices')
for voice in voices:
    print(f"Voice: {voice.name}")

# Set voice
engine.setProperty('voice', voices[0].id)

# Generate speech
engine.say("Warning! Person detected near entrance.")
engine.runAndWait()
```

**Option 2: gTTS (Google TTS, Better Quality)**
```python
from gtts import gTTS
import os

def generate_tts_gtts(text, output_file='alert.mp3'):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_file)
    return output_file
```

**Option 3: Festival (Linux, Open Source)**
```bash
echo "Warning! Person detected" | festival --tts
```

### 3.2 Message Templates

**Dynamic message generation**:
```python
message_templates = {
    'person_at_door': "Warning! Person detected at {location} at {time}.",
    'person_near_vehicle': "Alert! Person within {distance} meters of your {vehicle}.",
    'loitering': "Attention! Person has been at {location} for {duration} minutes.",
    'package_delivery': "Package delivered at {location}.",
    'animal_detected': "Animal detected: {animal_type} in {location}.",
}

def format_message(template_key, **kwargs):
    template = message_templates[template_key]
    return template.format(**kwargs)

# Usage
message = format_message('person_at_door', 
                        location='front door', 
                        time='11:30 PM')
# Output: "Warning! Person detected at front door at 11:30 PM."
```

### 3.3 Message Caching

**Pre-generate common messages**:
```python
class TTSCache:
    def __init__(self, cache_dir='data/tts_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load existing cached messages."""
        for file in self.cache_dir.glob('*.mp3'):
            key = file.stem
            self.cache[key] = str(file)
    
    def get_or_generate(self, text):
        """Get cached audio or generate new."""
        # Create hash of text
        key = hashlib.md5(text.encode()).hexdigest()
        
        if key in self.cache:
            return self.cache[key]
        
        # Generate new
        output_file = self.cache_dir / f"{key}.mp3"
        tts = gTTS(text=text, lang='en')
        tts.save(output_file)
        
        self.cache[key] = str(output_file)
        return str(output_file)
```

---

## 4. Speaker Interface Implementation

### 4.1 Abstract Speaker Interface

```python
from abc import ABC, abstractmethod

class SpeakerInterface(ABC):
    """Abstract base class for speaker implementations."""
    
    @abstractmethod
    def connect(self):
        """Connect to speaker."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from speaker."""
        pass
    
    @abstractmethod
    def is_connected(self):
        """Check if speaker is connected."""
        pass
    
    @abstractmethod
    def play(self, audio_file):
        """Play audio file through speaker."""
        pass
    
    @abstractmethod
    def set_volume(self, volume):
        """Set speaker volume (0.0 to 1.0)."""
        pass
```

### 4.2 Wired Speaker Implementation

```python
import pyaudio
import wave

class WiredSpeaker(SpeakerInterface):
    """Wired speaker via 3.5mm jack."""
    
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.pa = pyaudio.PyAudio()
        self.volume = 0.9
        self.connected = True
    
    def connect(self):
        """Connect to audio device."""
        # Already connected (system default)
        self.connected = True
        return True
    
    def disconnect(self):
        """Disconnect (no-op for wired)."""
        pass
    
    def is_connected(self):
        """Check connection status."""
        return self.connected
    
    def play(self, audio_file):
        """Play audio file."""
        try:
            wf = wave.open(audio_file, 'rb')
            
            stream = self.pa.open(
                format=self.pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.device_id
            )
            
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
            logger.info(f"Played audio: {audio_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        # Volume adjustment via alsaaudio (Linux) or system API
```

### 4.3 Bluetooth Speaker Implementation

```python
import bluetooth
import subprocess

class BluetoothSpeaker(SpeakerInterface):
    """Bluetooth speaker implementation."""
    
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.connected = False
        self.device_name = None
    
    def connect(self):
        """Connect to Bluetooth speaker."""
        try:
            # Use bluetoothctl for connection
            subprocess.run(['bluetoothctl', 'connect', self.mac_address], 
                          check=True, timeout=10)
            
            time.sleep(2)  # Wait for connection to establish
            
            # Verify connection
            self.connected = self._is_bluetooth_connected()
            
            if self.connected:
                logger.success(f"Connected to Bluetooth speaker: {self.mac_address}")
            else:
                logger.error(f"Failed to connect to Bluetooth speaker")
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Bluetooth connection error: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Bluetooth speaker."""
        try:
            subprocess.run(['bluetoothctl', 'disconnect', self.mac_address])
            self.connected = False
            logger.info("Disconnected from Bluetooth speaker")
        except Exception as e:
            logger.error(f"Bluetooth disconnection error: {e}")
    
    def is_connected(self):
        """Check if Bluetooth speaker is connected."""
        return self._is_bluetooth_connected()
    
    def _is_bluetooth_connected(self):
        """Check Bluetooth connection status."""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', self.mac_address],
                capture_output=True,
                text=True
            )
            return 'Connected: yes' in result.stdout
        except:
            return False
    
    def play(self, audio_file):
        """Play audio through Bluetooth speaker."""
        if not self.is_connected():
            logger.warning("Bluetooth speaker not connected, attempting reconnection...")
            if not self.connect():
                logger.error("Cannot play audio: speaker not connected")
                return False
        
        try:
            # Play using system audio player
            subprocess.run(['aplay', audio_file], check=True)
            logger.info(f"Played audio via Bluetooth: {audio_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to play audio via Bluetooth: {e}")
            return False
    
    def set_volume(self, volume):
        """Set Bluetooth speaker volume."""
        try:
            volume_percent = int(volume * 100)
            subprocess.run(['amixer', 'set', 'Master', f'{volume_percent}%'])
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
```

---

## 5. Alert Manager Implementation

### 5.1 Main Alert Manager

```python
class AlertManager:
    """Manages alert evaluation and delivery."""
    
    def __init__(self, config):
        self.config = config
        self.rules = self._load_rules()
        self.speakers = self._init_speakers()
        self.tts_cache = TTSCache()
        self.alert_queue = Queue()
        self.last_alert_times = {}
        
        # Start alert delivery thread
        self.running = True
        self.delivery_thread = threading.Thread(target=self._alert_delivery_loop, daemon=True)
        self.delivery_thread.start()
    
    def _load_rules(self):
        """Load alert rules from configuration."""
        rules = []
        for rule_config in self.config.get('alert_rules', []):
            rule = AlertRule(rule_config)
            rules.append(rule)
        return rules
    
    def _init_speakers(self):
        """Initialize all configured speakers."""
        speakers = {}
        for speaker_config in self.config.get('speakers', []):
            name = speaker_config['name']
            speaker_type = speaker_config['type']
            
            if speaker_type == 'wired':
                speaker = WiredSpeaker(speaker_config.get('device_id'))
            elif speaker_type == 'bluetooth':
                speaker = BluetoothSpeaker(speaker_config['mac_address'])
            elif speaker_type == 'group':
                # Group speaker references other speakers
                speaker = GroupSpeaker(speaker_config['speakers'], speakers)
            
            speakers[name] = speaker
        
        return speakers
    
    def evaluate(self, tracks, frame):
        """Evaluate tracks against all rules."""
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if not self._check_cooldown(rule):
                continue
            
            # Evaluate rule
            if rule.evaluate(tracks, frame):
                # Rule triggered
                alert = self._create_alert(rule, tracks, frame)
                self.alert_queue.put(alert)
                self.last_alert_times[rule.name] = time.time()
                
                logger.warning(f"Alert triggered: {rule.name}")
    
    def _check_cooldown(self, rule):
        """Check if rule is in cooldown period."""
        if rule.name not in self.last_alert_times:
            return True
        
        elapsed = time.time() - self.last_alert_times[rule.name]
        return elapsed >= rule.cooldown
    
    def _create_alert(self, rule, tracks, frame):
        """Create alert object from rule and trigger context."""
        return {
            'rule_name': rule.name,
            'timestamp': time.time(),
            'camera_id': frame.camera_id,
            'message': rule.message,
            'priority': rule.priority,
            'actions': rule.actions,
            'tracks': tracks
        }
    
    def _alert_delivery_loop(self):
        """Background thread for delivering alerts."""
        while self.running:
            try:
                # Get alert from queue (blocking with timeout)
                alert = self.alert_queue.get(timeout=1)
                
                # Execute alert actions
                self._execute_actions(alert)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in alert delivery: {e}")
    
    def _execute_actions(self, alert):
        """Execute all actions for an alert."""
        for action in alert['actions']:
            action_type = action['type']
            
            if action_type == 'audio_alert':
                self._play_audio_alert(alert, action)
            elif action_type == 'snapshot':
                self._save_snapshot(alert, action)
            elif action_type == 'log':
                self._log_alert(alert, action)
            elif action_type == 'email':
                self._send_email(alert, action)
    
    def _play_audio_alert(self, alert, action):
        """Play audio alert through speaker."""
        message = action['message']
        speaker_name = action.get('speaker', 'all')
        repeat = action.get('repeat', 1)
        
        # Generate or get cached audio
        audio_file = self.tts_cache.get_or_generate(message)
        
        # Get speaker(s)
        if speaker_name == 'all':
            speakers = list(self.speakers.values())
        else:
            speakers = [self.speakers.get(speaker_name)]
        
        # Play through each speaker
        for _ in range(repeat):
            for speaker in speakers:
                if speaker and speaker.is_connected():
                    speaker.play(audio_file)
                    time.sleep(0.5)  # Brief pause between repeats
    
    def stop(self):
        """Stop alert manager."""
        self.running = False
        if self.delivery_thread:
            self.delivery_thread.join(timeout=2)
```

---

## 6. Alert Testing

### 6.1 Test Script

```python
# scripts/test_alerts.py
def test_alert_system():
    """Test alert delivery."""
    config = ConfigLoader('config/config.yaml')
    alert_manager = AlertManager(config)
    
    # Create test alert
    test_alert = {
        'rule_name': 'test',
        'timestamp': time.time(),
        'camera_id': 'test',
        'message': 'This is a test alert. Please confirm you can hear this.',
        'priority': 'high',
        'actions': [
            {
                'type': 'audio_alert',
                'message': 'Test alert. Can you hear this?',
                'speaker': 'living_room',
                'repeat': 1
            }
        ],
        'tracks': []
    }
    
    # Deliver alert
    alert_manager._execute_actions(test_alert)
    
    print("Test alert sent. Did you hear it? (yes/no)")
    response = input().lower()
    
    return response == 'yes'
```

---

## 7. Advanced Features

### 7.1 Multi-Language Support

```python
# config/messages.yaml
messages:
  en:
    person_at_door: "Warning! Person detected at entrance."
    vehicle_alert: "Alert! Person near your vehicle."
  es:
    person_at_door: "¡Advertencia! Persona detectada en la entrada."
    vehicle_alert: "¡Alerta! Persona cerca de su vehículo."
```

### 7.2 Custom Sound Effects

```python
sound_effects = {
    'critical': 'sounds/siren.wav',
    'high': 'sounds/beep.wav',
    'medium': 'sounds/chime.wav'
}

def play_alert_with_sound(priority, message):
    # Play sound effect first
    play_sound(sound_effects[priority])
    time.sleep(0.5)
    # Then play message
    play_tts(message)
```

This comprehensive alert system ensures users are immediately and clearly informed of security events.
