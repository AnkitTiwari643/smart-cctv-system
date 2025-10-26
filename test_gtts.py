#!/usr/bin/env python3
"""
Test script to verify gtts TTS engine implementation.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_gtts_tts():
    """Test gtts TTS engine."""
    
    print("Testing gtts TTS Engine Implementation...")
    print("=" * 50)
    
    try:
        from src.utils.audio_utils import TTSEngine
        
        # Test 1: Basic gtts configuration
        print("\n1. Testing basic gtts configuration:")
        config = {
            "engine": "gtts",
            "language": "en",
            "cache_enabled": True,
            "cache_dir": "./data/tts_cache"
        }
        
        try:
            tts = TTSEngine(config)
            print("✅ gtts TTS engine initialized successfully")
            
            # Test speaking
            print("2. Testing speech generation:")
            success = tts.speak("Hello, this is a test of the gtts text to speech system.", blocking=True)
            if success:
                print("✅ Speech generation successful")
            else:
                print("❌ Speech generation failed")
                
        except Exception as e:
            print(f"❌ gtts initialization failed: {e}")
        
        # Test 3: Different languages
        print("\n3. Testing different language (Spanish):")
        config_es = {
            "engine": "gtts",
            "language": "es",
            "cache_enabled": True,
            "cache_dir": "./data/tts_cache"
        }
        
        try:
            tts_es = TTSEngine(config_es)
            success = tts_es.speak("Hola, esto es una prueba del sistema de texto a voz.", blocking=True)
            if success:
                print("✅ Spanish speech generation successful")
            else:
                print("❌ Spanish speech generation failed")
        except Exception as e:
            print(f"❌ Spanish gtts failed: {e}")
            
        # Test 4: Check cache directory
        print("\n4. Checking cache directory:")
        cache_dir = Path("./data/tts_cache")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.mp3"))
            print(f"✅ Cache directory exists with {len(cache_files)} cached files")
        else:
            print("❌ Cache directory not found")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure gtts is installed: pip install gtts")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("gtts TTS Engine Test Complete!")

def check_dependencies():
    """Check if required dependencies are available."""
    print("Checking dependencies...")
    
    try:
        from gtts import gTTS
        print("✅ gtts is available")
    except ImportError:
        print("❌ gtts not found. Install with: pip install gtts")
        return False
    
    try:
        import pygame
        print("✅ pygame is available")
    except ImportError:
        print("⚠️  pygame not found. Install with: pip install pygame")
    
    try:
        from loguru import logger
        print("✅ loguru is available")
    except ImportError:
        print("❌ loguru not found. Install with: pip install loguru")
        return False
    
    return True

if __name__ == "__main__":
    if check_dependencies():
        test_gtts_tts()
    else:
        print("Please install missing dependencies first.")