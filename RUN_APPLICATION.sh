#!/bin/bash

# GPTGRAM COMPLETE APPLICATION STARTUP SCRIPT
# This script starts both backend and frontend services

echo "========================================="
echo "🚀 STARTING GPTGRAM APPLICATION"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kill any existing processes
echo -e "${YELLOW}Stopping existing services...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 2

# Start Backend
echo -e "${YELLOW}Starting Backend...${NC}"
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 test_server.py > /tmp/gptgram_backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Check if backend started
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend started successfully (PID: $BACKEND_PID)${NC}"
    echo -e "   URL: http://localhost:8000"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "   Check logs: tail -f /tmp/gptgram_backend.log"
    exit 1
fi

# Build Frontend (if needed)
echo -e "${YELLOW}Building Frontend...${NC}"
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
npm run build > /tmp/gptgram_build.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend built successfully${NC}"
else
    echo -e "${RED}❌ Frontend build failed${NC}"
    echo "   Check logs: tail -f /tmp/gptgram_build.log"
    exit 1
fi

# Start Frontend
echo -e "${YELLOW}Starting Frontend...${NC}"
npm run dev > /tmp/gptgram_frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 5

# Check if frontend started
if lsof -i:3000 | grep LISTEN > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
    echo -e "   URL: http://localhost:3000"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
    echo "   Check logs: tail -f /tmp/gptgram_frontend.log"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ GPTGRAM APPLICATION RUNNING"
echo "========================================="
echo ""
echo "🌐 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:8000"
echo ""
echo "📝 Login Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "📊 Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📋 View Logs:"
echo "   Backend:  tail -f /tmp/gptgram_backend.log"
echo "   Frontend: tail -f /tmp/gptgram_frontend.log"
echo ""
echo "🛑 To Stop:"
echo "   lsof -ti:8000 | xargs kill -9"
echo "   lsof -ti:3000 | xargs kill -9"
echo ""
echo "========================================="
echo "🎉 READY TO USE!"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Press Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows) to hard refresh"
echo "3. Login with demo / demo123"
echo "4. Go to Chain Builder to see agent library"
echo ""
