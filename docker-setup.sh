#!/bin/bash
# Setup script for Smart CCTV System Docker deployment

echo "🐳 Smart CCTV System - Docker Setup"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the smart-cctv-system directory"
    exit 1
fi

echo "📋 Pre-flight checklist:"

# 1. Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✅ Docker installed"

# 2. Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi
echo "✅ Docker Compose installed"

# 3. Create necessary directories
echo "📁 Creating required directories..."
mkdir -p config data models
mkdir -p data/logs data/snapshots data/tts_cache
echo "✅ Directories created"

# 4. Setup configuration
echo "⚙️ Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    if [ -f "config/config.example.yaml" ]; then
        cp config/config.example.yaml config/config.yaml
        echo "✅ Created config/config.yaml from example"
        echo "📝 You need to edit config/config.yaml with your camera settings"
        
        # Ask if user wants to edit now
        read -p "Do you want to edit the configuration now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v nano &> /dev/null; then
                nano config/config.yaml
            elif command -v vi &> /dev/null; then
                vi config/config.yaml
            else
                echo "⚠️ No text editor found. Please edit config/config.yaml manually"
            fi
        else
            echo "📝 Remember to edit config/config.yaml before running the system"
        fi
    else
        echo "❌ config/config.example.yaml not found"
        exit 1
    fi
else
    echo "✅ Configuration file already exists"
fi

# 5. Set proper permissions
echo "🔒 Setting permissions..."
chmod -R 755 data models || true
echo "✅ Permissions set"

# 6. Create .env file for environment variables
echo "🔐 Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Camera passwords (change these!)
CAMERA_1_PASSWORD=changeme
CAMERA_2_PASSWORD=changeme
CAMERA_3_PASSWORD=changeme
CAMERA_4_PASSWORD=changeme

# Timezone
TZ=America/New_York
EOF
    echo "✅ Created .env file with default values"
    echo "🔐 Please edit .env file to set your camera passwords"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config/config.yaml with your camera URLs and settings"
echo "2. Edit .env file to set camera passwords"
echo "3. Run: docker-compose up --build"
echo ""
echo "Troubleshooting:"
echo "• Check logs: docker-compose logs -f"
echo "• Restart: docker-compose restart"
echo "• Stop: docker-compose down"
echo ""

# Option to start immediately
read -p "Do you want to start the system now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting Smart CCTV System..."
    docker-compose up --build
fi