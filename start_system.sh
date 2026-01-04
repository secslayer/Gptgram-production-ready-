#!/bin/bash

echo "========================================="
echo "🚀 Starting GPTGram System"
echo "========================================="
echo ""

# Kill existing processes
echo "Stopping existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 2

# Start backend
echo "Starting backend..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 test_server.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend running on port 8000"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend
echo "Starting frontend..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 5

# Check frontend
if lsof -i:3000 | grep LISTEN > /dev/null; then
    echo "✅ Frontend running on port 3000"
else
    echo "❌ Frontend failed to start"
    echo "Check logs: tail -f /tmp/frontend.log"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ System Ready!"
echo "========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Login: demo / demo123"
echo ""
echo "Logs:"
echo "  Backend:  tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo ""
echo "========================================="
