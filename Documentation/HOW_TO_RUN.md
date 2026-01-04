# 🚀 HOW TO RUN GPTGRAM APPLICATION

## 📋 Complete Step-by-Step Guide

---

## METHOD 1: AUTOMATED STARTUP (RECOMMENDED)

### **Single Command Startup:**

```bash
# Make script executable
chmod +x /Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh

# Run the application
/Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh
```

This will:
- ✅ Stop any existing services
- ✅ Start backend on port 8000
- ✅ Build frontend
- ✅ Start frontend on port 3000
- ✅ Show you all URLs and credentials

---

## METHOD 2: MANUAL STARTUP

### **Step 1: Start Backend**

```bash
# Navigate to backend directory
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend

# Start the backend server
python3 test_server.py
```

**Expected Output:**
```
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Verify Backend:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","timestamp":"..."}
```

---

### **Step 2: Start Frontend**

**Open a NEW terminal**, then:

```bash
# Navigate to frontend directory
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend

# Install dependencies (first time only)
npm install

# Build the application
npm run build

# Start development server
npm run dev
```

**Expected Output:**
```
VITE v5.4.21 ready in XXX ms
➜ Local:   http://localhost:3000/
```

**Verify Frontend:**
```bash
curl -I http://localhost:3000
# Should return: HTTP/1.1 200 OK
```

---

## 🌐 ACCESS THE APPLICATION

### **URL:**
```
http://localhost:3000
```

### **Login Credentials:**
```
Username: demo
Password: demo123
```

### **IMPORTANT: Hard Refresh After Login**
```
Mac:     Cmd + Shift + R
Windows: Ctrl + Shift + R
Linux:   Ctrl + Shift + R
```

---

## 🔧 FIX AGENT LIBRARY NOT UPDATING

### **Problem:**
Agent library in Chain Builder doesn't show new agents immediately.

### **Solution:**

The Chain Builder has auto-refresh enabled, but if you're not seeing updates:

#### **Option 1: Manual Refresh (Immediate)**
1. Go to Chain Builder (`/chains`)
2. Look at right panel "Agent Library"
3. Click **"Refresh Agents (X)"** button
4. Should show updated count and new agents

#### **Option 2: Wait for Auto-Refresh**
- Automatic refresh: Every **5 seconds**
- Just wait a few moments

#### **Option 3: Switch Tabs**
- Switch to another browser tab
- Switch back to GPTGram tab
- Triggers immediate refresh

#### **Option 4: Hard Refresh Browser**
```
Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

---

## 🧪 TEST AGENT LIBRARY REFRESH

### **Quick Test:**

```bash
# Run this test script
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/TEST_AGENT_REFRESH.py
```

This will:
1. Show current agent count
2. Create a new test agent
3. Verify it appears in API
4. Guide you through browser verification

---

## 📊 VERIFY EVERYTHING IS WORKING

### **Run Verification Script:**

```bash
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/QUICK_VERIFY.py
```

**Expected Output:**
```
✅ Backend: RUNNING
✅ Frontend: RUNNING
✅ Agents: X in system
✅ Runs: X executed
```

---

## 🎯 COMMON PAGES TO TEST

### **1. Dashboard** (`/`)
- Shows agent count
- Shows run statistics
- Wallet balance

### **2. Chain Builder** (`/chains`)
- Agent Library on right panel
- Shows "Available Agents (X)"
- Can drag agents to canvas
- **Refresh Agents button**

### **3. Run History** (`/runs`)
- Shows executed chains
- Timeline with timestamps
- No "None" values

### **4. Code Fuser** (`/code-fuser`)
- Dropdown shows all agents
- Generate Python/JavaScript/cURL code

### **5. Marketplace** (`/marketplace`)
- Browse all agents
- Prices displayed
- Search and filter

### **6. My Agents** (`/agents`)
- View all agents
- Create new agents
- Delete agents

---

## 🛑 STOP THE APPLICATION

### **Method 1: Kill by Port**
```bash
# Stop backend
lsof -ti:8000 | xargs kill -9

# Stop frontend
lsof -ti:3000 | xargs kill -9
```

### **Method 2: Kill by Process**
```bash
# Find processes
ps aux | grep "test_server.py"
ps aux | grep "vite"

# Kill them
kill -9 <PID>
```

---

## 📝 TROUBLESHOOTING

### **Issue: Backend not starting**

```bash
# Check if port is in use
lsof -i:8000

# Kill existing process
lsof -ti:8000 | xargs kill -9

# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
cd backend
pip3 install -r requirements.txt

# Try starting again
python3 test_server.py
```

---

### **Issue: Frontend not starting**

```bash
# Check if port is in use
lsof -i:3000

# Kill existing process
lsof -ti:3000 | xargs kill -9

# Check Node version
node --version  # Should be 16+
npm --version

# Clean install
cd frontend
rm -rf node_modules
rm package-lock.json
npm install

# Try starting again
npm run dev
```

---

### **Issue: Agent Library not updating**

**Immediate Fixes:**

1. **Click Refresh Button:**
   - Go to Chain Builder
   - Click "Refresh Agents (X)" button

2. **Check Console:**
   - Press F12 in browser
   - Go to Console tab
   - Look for "Loaded agents: X agents"
   - Should update every 5 seconds

3. **Verify API:**
   ```bash
   curl http://localhost:8000/api/agents
   ```
   - Should return JSON array of agents

4. **Hard Refresh:**
   - Cmd+Shift+R or Ctrl+Shift+R

---

### **Issue: Blank Page**

**Solution:**

1. **Hard refresh browser:**
   ```
   Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
   ```

2. **Clear browser cache:**
   - Settings → Clear browsing data
   - Select "Cached images and files"
   - Clear data

3. **Check browser console (F12):**
   - Look for errors in Console tab
   - Look for failed network requests

4. **Verify frontend is built:**
   ```bash
   cd frontend
   npm run build
   npm run dev
   ```

---

## 📊 SYSTEM REQUIREMENTS

### **Backend:**
- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic

### **Frontend:**
- Node.js 16+
- npm 8+
- Vite
- React

### **Ports:**
- **8000** - Backend API
- **3000** - Frontend UI

---

## 🎯 COMPLETE STARTUP CHECKLIST

- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Ports 8000 and 3000 are available
- [ ] Backend started (http://localhost:8000)
- [ ] Frontend started (http://localhost:3000)
- [ ] Can access login page
- [ ] Can login with demo/demo123
- [ ] Dashboard loads
- [ ] Chain Builder shows agent library
- [ ] Agent library has "Refresh Agents" button
- [ ] Agents auto-refresh every 5 seconds

---

## 🚀 QUICK START COMMANDS

```bash
# One-line startup
chmod +x /Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh && /Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh

# Check status
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/QUICK_VERIFY.py

# Test agent refresh
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/TEST_AGENT_REFRESH.py

# View logs
tail -f /tmp/gptgram_backend.log
tail -f /tmp/gptgram_frontend.log

# Stop everything
lsof -ti:8000 | xargs kill -9; lsof -ti:3000 | xargs kill -9
```

---

## ✅ VERIFICATION STEPS

After starting the application:

1. **Open:** http://localhost:3000
2. **Login:** demo / demo123
3. **Hard Refresh:** Cmd+Shift+R
4. **Go to Chain Builder:** `/chains`
5. **Check Agent Library:** Right panel shows agents
6. **Click Refresh:** Should show agent count
7. **Create New Agent:** Go to `/agents`, create one
8. **Return to Chain Builder:** Wait 5 seconds or click refresh
9. **Verify:** New agent appears in library

---

## 🎉 YOU'RE READY!

The application should now be running with:
- ✅ Backend API responding
- ✅ Frontend UI accessible
- ✅ Agent library auto-refreshing
- ✅ All features working

**Open http://localhost:3000 and start building agent chains!**
