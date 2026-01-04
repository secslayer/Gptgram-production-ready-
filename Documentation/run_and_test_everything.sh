#!/bin/bash

echo "=================================================="
echo "🚀 COMPLETE SYSTEM STARTUP AND COMPREHENSIVE TEST"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check if port is open
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Step 1: Kill existing processes
echo "1️⃣ Cleaning up existing processes..."
pkill -f test_server.py
pkill -f "npm.*dev"
pkill -f "vite"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
sleep 3

# Step 2: Start Backend
echo ""
echo "2️⃣ Starting Backend Server..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend

# Start server
python3 test_server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
echo -n "   Waiting for backend to start"
for i in {1..10}; do
    sleep 1
    echo -n "."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✅ Ready${NC}"
        break
    fi
done

# Verify backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "   ${RED}❌ Backend failed to start${NC}"
    echo "   Check backend.log for errors"
    exit 1
fi

# Step 3: Build Frontend
echo ""
echo "3️⃣ Building Frontend..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

# Build frontend
echo -n "   Building"
npm run build > frontend_build.log 2>&1 &
BUILD_PID=$!

# Wait for build with spinner
for i in {1..30}; do
    if ! kill -0 $BUILD_PID 2>/dev/null; then
        break
    fi
    echo -n "."
    sleep 1
done

# Check if build succeeded
if wait $BUILD_PID; then
    echo -e " ${GREEN}✅ Build successful${NC}"
else
    echo -e " ${RED}❌ Build failed${NC}"
    echo "   Check frontend_build.log for errors"
    cat frontend_build.log | tail -20
fi

# Step 4: Start Frontend Dev Server
echo ""
echo "4️⃣ Starting Frontend Dev Server..."
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
echo -n "   Waiting for frontend to start"
for i in {1..15}; do
    sleep 1
    echo -n "."
    if check_port 3000 || check_port 5173; then
        echo -e " ${GREEN}✅ Ready${NC}"
        break
    fi
done

# Determine frontend URL
FRONTEND_URL=""
if check_port 5173; then
    FRONTEND_URL="http://localhost:5173"
elif check_port 3000; then
    FRONTEND_URL="http://localhost:3000"
fi

if [ -z "$FRONTEND_URL" ]; then
    echo -e "   ${RED}❌ Frontend failed to start${NC}"
    echo "   Check frontend.log for errors"
    exit 1
fi

echo "   Frontend running at: $FRONTEND_URL"

# Step 5: Run API Tests First
echo ""
echo "5️⃣ Running Backend API Tests..."
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend

python3 tests/final_complete_test.py > api_test_results.log 2>&1
API_TEST_RESULT=$?

if [ $API_TEST_RESULT -eq 0 ]; then
    echo -e "   ${GREEN}✅ API tests passed${NC}"
    cat api_test_results.log | grep "SUCCESS:" | tail -1
else
    echo -e "   ${YELLOW}⚠️ Some API tests failed${NC}"
    cat api_test_results.log | grep "FAILED:" | tail -5
fi

# Step 6: Install Selenium dependencies if needed
echo ""
echo "6️⃣ Checking Selenium Dependencies..."
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "   Installing selenium..."
    pip3 install selenium
fi

# Check for ChromeDriver
if ! which chromedriver > /dev/null; then
    echo -e "   ${YELLOW}⚠️ ChromeDriver not found${NC}"
    echo "   Installing with Homebrew..."
    brew install --cask chromedriver 2>/dev/null || true
fi

# Step 7: Run Comprehensive Selenium Tests
echo ""
echo "7️⃣ Running Comprehensive System Tests with Selenium..."
echo "   This will test:"
echo "   • Frontend components"
echo "   • Backend integration"
echo "   • Agent creation and verification"
echo "   • Chain building with React Flow"
echo "   • Moderator functionality"
echo "   • Run history"
echo "   • Dashboard real data"
echo ""

# Update the test to use correct frontend URL
export FRONTEND_URL=$FRONTEND_URL
python3 tests/comprehensive_system_test.py > selenium_test_results.log 2>&1
SELENIUM_TEST_RESULT=$?

# Show test results
echo ""
if [ $SELENIUM_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All Selenium tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️ Some Selenium tests failed${NC}"
fi

# Display test summary
cat selenium_test_results.log | grep -A 10 "COMPREHENSIVE TEST RESULTS" | tail -15

# Step 8: Final Summary
echo ""
echo "=================================================="
echo "📊 FINAL SYSTEM STATUS"
echo "=================================================="
echo ""

# Check all services
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "✅ Backend: ${GREEN}Running${NC} at http://localhost:8000"
    
    # Check key endpoints
    endpoints=("/api/agents/" "/api/moderator/logs" "/api/runs/" "/api/wallet/balance")
    for endpoint in "${endpoints[@]}"; do
        if curl -s "http://localhost:8000$endpoint" > /dev/null 2>&1; then
            echo -e "   ✅ $endpoint: ${GREEN}Working${NC}"
        else
            echo -e "   ❌ $endpoint: ${RED}Not responding${NC}"
        fi
    done
else
    echo -e "❌ Backend: ${RED}Not running${NC}"
fi

echo ""
if [ ! -z "$FRONTEND_URL" ]; then
    echo -e "✅ Frontend: ${GREEN}Running${NC} at $FRONTEND_URL"
else
    echo -e "❌ Frontend: ${RED}Not running${NC}"
fi

# Display logs location
echo ""
echo "📁 Logs available at:"
echo "   • Backend: /Users/abdulmuiz/Documents/LAB/Gptgram/backend/backend.log"
echo "   • Frontend: /Users/abdulmuiz/Documents/LAB/Gptgram/frontend/frontend.log"
echo "   • API Tests: /Users/abdulmuiz/Documents/LAB/Gptgram/backend/api_test_results.log"
echo "   • Selenium Tests: /Users/abdulmuiz/Documents/LAB/Gptgram/backend/selenium_test_results.log"

echo ""
echo "🔧 To stop all services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=================================================="

# Keep script running to maintain processes
echo ""
echo "Press Ctrl+C to stop all services..."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Services stopped'; exit" INT
wait
