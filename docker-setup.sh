#!/bin/bash
# Setup script for Smart CCTV System Docker deployment with Web Interface

echo "🐳 Smart CCTV System - Docker Setup with Web Interface"
echo "====================================================="

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
mkdir -p data/logs data/snapshots data/tts_cache data/web
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
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "🔐 Please edit .env file to customize settings"
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || date +%s | sha256sum | base64 | head -c 32)
    sed -i.bak "s/your-very-secure-secret-key-here-change-this/$SECRET_KEY/" .env 2>/dev/null || true
    
    echo "🔑 Generated random secret key for web interface"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🌟 Available Services:"
echo "• Complete System: docker-compose up"
echo "• Demo Mode: docker-compose --profile demo up" 
echo "• Web Interface Only: docker-compose --profile web-only up"
echo ""
echo "🌐 Web Interface Features:"
echo "• Dashboard: Real-time monitoring"
echo "• Configuration: Easy YAML editing"
echo "• Alerts: Manage security alerts"
echo "• Cameras: Live feed monitoring"
echo "• System: Performance monitoring"
echo ""
echo "� Access URLs:"
echo "• Web Interface: http://localhost:5000"
echo "• Default Login: admin / admin123"
echo ""
echo "Next steps:"
echo "1. Edit config/config.yaml with your camera URLs and settings"
echo "2. Edit .env file to customize security settings"
echo "3. Choose a deployment option below"
echo ""
echo "Deployment Options:"
echo "a) Complete System (CCTV detection + Web UI)"
echo "b) Demo Mode (Sample data for testing)"
echo "c) Web Interface Only"
echo "d) Exit for manual setup"
echo ""

# Deployment option selection
read -p "Select deployment option (a/b/c/d): " -n 1 -r
echo
case $REPLY in
    a|A)
        echo "🚀 Starting Complete Smart CCTV System..."
        docker-compose up --build
        ;;
    b|B)
        echo "🎬 Starting Demo Mode with Sample Data..."
        docker-compose --profile demo up --build
        ;;
    c|C)
        echo "🌐 Starting Web Interface Only..."
        docker-compose --profile web-only up --build
        ;;
    d|D)
        echo "✋ Manual setup chosen"
        echo "Run 'docker-compose up --build' when ready"
        ;;
    *)
        echo "Invalid option. Run 'docker-compose up --build' when ready"
        ;;
esac