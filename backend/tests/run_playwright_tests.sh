#!/bin/bash

echo "================================================="
echo "🎭 PLAYWRIGHT TEST RUNNER FOR GPTGRAM"
echo "================================================="

# Install Playwright if needed
echo "1️⃣ Checking Playwright installation..."
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "Installing Playwright..."
    pip3 install playwright pytest-playwright
    python3 -m playwright install chromium
else
    echo "✅ Playwright is installed"
fi

# Check if backend is running
echo ""
echo "2️⃣ Checking backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "⚠️ Starting backend..."
    cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
    python3 test_server.py > backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 5
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend started (PID: $BACKEND_PID)"
    else
        echo "❌ Backend failed to start"
        exit 1
    fi
fi

# Check if frontend is running
echo ""
echo "3️⃣ Checking frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1 || curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
    
    # Detect which port
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        export FRONTEND_URL="http://localhost:5173"
    else
        export FRONTEND_URL="http://localhost:3000"
    fi
else
    echo "⚠️ Starting frontend..."
    cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    sleep 8
    
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✅ Frontend started at :5173 (PID: $FRONTEND_PID)"
        export FRONTEND_URL="http://localhost:5173"
    elif curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend started at :3000 (PID: $FRONTEND_PID)"
        export FRONTEND_URL="http://localhost:3000"
    else
        echo "❌ Frontend failed to start"
        exit 1
    fi
fi

echo "Frontend URL: $FRONTEND_URL"

# Run Playwright tests
echo ""
echo "4️⃣ Running Playwright tests..."
echo "================================================="
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend/tests
python3 playwright_test_suite.py

TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
fi

echo "================================================="
exit $TEST_RESULT
