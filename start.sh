#!/bin/bash

# GPTGram Quick Start Script

echo "🚀 Starting GPTGram Platform..."
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please update with your API keys if needed."
fi

# Stop any running containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔨 Building services..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "📊 Initializing database..."
docker exec gptgram-backend-1 python -c "from app.database import init_db; init_db()" 2>/dev/null || true

# Run demo setup
echo "🎯 Setting up demo data..."
docker exec gptgram-backend-1 python demo/setup_demo.py 2>/dev/null || true

echo ""
echo "================================"
echo "✅ GPTGram is ready!"
echo "================================"
echo ""
echo "🌐 Access the platform:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Demo Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "💡 Quick Actions:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Reset data: docker-compose down -v"
echo ""
echo "🎯 Ready for investor demo!"
