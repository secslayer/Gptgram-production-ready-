#!/bin/bash

echo "🚀 STARTING COMPLETE GPTGRAM SYSTEM"
echo "===================================="

# Step 1: Kill any existing processes
echo "1️⃣ Cleaning up old processes..."
pkill -f test_server.py
pkill -f "python.*test_server"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 2

# Step 2: Start backend
echo "2️⃣ Starting backend server..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 test_server.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
sleep 5

# Step 3: Verify backend is running
echo "3️⃣ Verifying backend..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend failed to start"
    exit 1
fi

# Step 4: Start frontend
echo "4️⃣ Starting frontend..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
sleep 5

# Step 5: Run tests
echo "5️⃣ Running system tests..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 tests/final_complete_test.py

# Step 6: Display status
echo ""
echo "===================================="
echo "📊 SYSTEM STATUS"
echo "===================================="
echo "✅ Backend: http://localhost:8000"
echo "✅ Frontend: http://localhost:3000"
echo "✅ Health: http://localhost:8000/health"
echo "✅ Agents: http://localhost:8000/api/agents/"
echo "✅ Moderator: http://localhost:8000/api/moderator/logs"
echo ""
echo "📝 To stop the system:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "===================================="
