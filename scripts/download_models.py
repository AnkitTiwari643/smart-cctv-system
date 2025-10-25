#!/usr/bin/env python3
"""
Download YOLO models for the Smart CCTV system.
This script can be run separately to pre-download models.
"""
import os
import sys
import requests
import ssl
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError

# Model URLs and info
YOLO_MODELS = {
    "yolov8n.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt",
        "size": "6MB",
        "description": "Nano - Fastest, good for real-time"
    },
    "yolov8s.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt", 
        "size": "22MB",
        "description": "Small - Balanced speed/accuracy"
    },
    "yolov8m.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8m.pt",
        "size": "52MB", 
        "description": "Medium - Higher accuracy"
    },
    "yolov8l.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8l.pt",
        "size": "87MB",
        "description": "Large - Highest accuracy"
    }
}


def download_with_progress(url: str, filepath: str):
    """Download file with progress bar."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print()  # New line after progress
        return True
        
    except Exception as e:
        print(f"\n  Error downloading: {e}")
        return False


def download_model(model_name: str, models_dir: str = "models", force: bool = False):
    """Download a specific YOLO model."""
    
    if model_name not in YOLO_MODELS:
        print(f"❌ Unknown model: {model_name}")
        print(f"Available models: {list(YOLO_MODELS.keys())}")
        return False
    
    model_info = YOLO_MODELS[model_name]
    filepath = os.path.join(models_dir, model_name)
    
    # Check if already exists
    if os.path.exists(filepath) and not force:
        file_size = os.path.getsize(filepath)
        print(f"✓ {model_name} already exists ({file_size} bytes)")
        return True
    
    print(f"📥 Downloading {model_name} ({model_info['size']}) - {model_info['description']}")
    print(f"   URL: {model_info['url']}")
    print(f"   Destination: {filepath}")
    
    # Create models directory
    os.makedirs(models_dir, exist_ok=True)
    
    # Try download
    success = download_with_progress(model_info['url'], filepath)
    
    if success:
        file_size = os.path.getsize(filepath)
        print(f"✅ {model_name} downloaded successfully ({file_size} bytes)")
        return True
    else:
        # Cleanup failed download
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"❌ Failed to download {model_name}")
        return False


def download_all_models(models_dir: str = "models", models: list = None):
    """Download all or specified YOLO models."""
    
    if models is None:
        models = ["yolov8n.pt"]  # Default to nano model only
    
    print(f"🤖 YOLO Model Downloader")
    print(f"Models directory: {os.path.abspath(models_dir)}")
    print(f"Models to download: {models}")
    print()
    
    success_count = 0
    total_count = len(models)
    
    for model_name in models:
        if download_model(model_name, models_dir):
            success_count += 1
        print()  # Spacing between models
    
    print(f"📊 Download Summary: {success_count}/{total_count} models downloaded successfully")
    
    if success_count == 0:
        print("\n🔧 Troubleshooting:")
        print("1. Check internet connection")
        print("2. Try running with --insecure flag")
        print("3. Download manually:")
        for model_name in models:
            if model_name in YOLO_MODELS:
                print(f"   wget {YOLO_MODELS[model_name]['url']} -O {models_dir}/{model_name}")
    
    return success_count == total_count


def list_models():
    """List available YOLO models."""
    print("📋 Available YOLO Models:")
    print()
    
    for model_name, info in YOLO_MODELS.items():
        print(f"  {model_name:<12} - {info['size']:<6} - {info['description']}")
    
    print()
    print("Usage examples:")
    print("  python download_models.py --model yolov8n.pt")
    print("  python download_models.py --all")
    print("  python download_models.py --model yolov8n.pt --model yolov8s.pt")


def test_ultralytics():
    """Test if ultralytics can load the downloaded models."""
    print("🧪 Testing model loading with ultralytics...")
    
    try:
        from ultralytics import YOLO
        
        models_dir = "models"
        available_models = [f for f in os.listdir(models_dir) if f.endswith('.pt')] if os.path.exists(models_dir) else []
        
        if not available_models:
            print("❌ No models found to test")
            return False
        
        for model_file in available_models:
            try:
                model_path = os.path.join(models_dir, model_file)
                print(f"  Testing {model_file}...")
                model = YOLO(model_path)
                print(f"  ✅ {model_file} loaded successfully")
            except Exception as e:
                print(f"  ❌ {model_file} failed to load: {e}")
        
        return True
        
    except ImportError:
        print("❌ ultralytics not installed. Install with: pip install ultralytics")
        return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download YOLO models for Smart CCTV system")
    parser.add_argument("--model", action="append", help="Specific model to download (can be used multiple times)")
    parser.add_argument("--all", action="store_true", help="Download all models")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--test", action="store_true", help="Test loading downloaded models")
    parser.add_argument("--models-dir", default="models", help="Directory to store models")
    parser.add_argument("--force", action="store_true", help="Force re-download existing models")
    parser.add_argument("--insecure", action="store_true", help="Skip SSL certificate verification")
    
    args = parser.parse_args()
    
    # Handle SSL issues if requested
    if args.insecure:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print("⚠️  SSL certificate verification disabled")
    
    if args.list:
        list_models()
        return 0
    
    if args.test:
        success = test_ultralytics()
        return 0 if success else 1
    
    # Determine which models to download
    if args.all:
        models_to_download = list(YOLO_MODELS.keys())
    elif args.model:
        models_to_download = args.model
    else:
        # Default: download nano model
        models_to_download = ["yolov8n.pt"]
        print("No specific models requested, downloading default: yolov8n.pt")
        print("Use --help to see other options")
        print()
    
    # Download models
    success = download_all_models(args.models_dir, models_to_download)
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)