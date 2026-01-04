#!/bin/bash
# Kill any existing server processes
echo "🔄 Killing existing server processes..."
pkill -f test_server.py
pkill -f "python.*test_server"
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Wait for port to be free
sleep 3

# Start server
echo "🚀 Starting server..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 test_server.py &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Server started successfully (PID: $SERVER_PID)"
else
    echo "❌ Server failed to start"
    exit 1
fi
