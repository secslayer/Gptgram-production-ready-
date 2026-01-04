# ✅ GPTGRAM COMPLETE GUIDE

## 🚀 QUICK START - HOW TO RUN

### **Method 1: One Command (EASIEST)**

```bash
/Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh
```

This automatically:
- Stops any running services
- Starts backend on port 8000
- Builds frontend
- Starts frontend on port 3000

---

### **Method 2: Manual Steps**

#### **Terminal 1 - Backend:**
```bash
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 test_server.py
```

#### **Terminal 2 - Frontend:**
```bash
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
npm run dev
```

---

## 🌐 ACCESS THE APPLICATION

**URL:** http://localhost:3000  
**Username:** demo  
**Password:** demo123

**IMPORTANT:** Hard refresh after login:
- Mac: `Cmd + Shift + R`
- Windows: `Ctrl + Shift + R`

---

## 📊 CURRENT SYSTEM STATE

✅ **Backend:** Running on port 8000  
✅ **Frontend:** Running on port 3000  
✅ **Agents:** 6 created  
✅ **Runs:** 1 executed  
✅ **Wallet:** $50.00

### **Available Agents:**
1. AI Text Summarizer - 50¢
2. Sentiment Analyzer Plus - 35¢
3. Language Translator Pro - 65¢
4. Keyword Extractor - 40¢
5. Content Classifier - 30¢
6. Data Formatter - 20¢

---

## 🔧 AGENT LIBRARY REFRESH - SOLUTION

### **Problem:** 
Agent library not showing new agents in Chain Builder

### **Solutions (in order of speed):**

#### **1. Click Refresh Button (Immediate)**
- Go to Chain Builder (`/chains`)
- Look at right panel
- Click **"Refresh Agents (6)"** button
- New agents appear immediately

#### **2. Wait 5 Seconds (Automatic)**
- Agent library auto-refreshes every 5 seconds
- No action needed, just wait

#### **3. Switch Browser Tabs (Immediate)**
- Click another browser tab
- Click back to GPTGram tab
- Triggers immediate refresh

#### **4. Hard Refresh Browser (Immediate)**
- Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

---

## 🧪 TEST AGENT LIBRARY REFRESH

### **Live Test:**

```bash
# This creates a new agent and verifies it appears
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/TEST_AGENT_REFRESH.py
```

**Steps:**
1. Run the test script
2. It creates a new test agent
3. Open browser to http://localhost:3000/chains
4. Watch agent library update within 5 seconds
5. Or click "Refresh Agents" button

---

## 📋 ALL PAGES TO VERIFY

### **1. Dashboard** (`/`)
- ✅ Shows 6 agents
- ✅ Shows 1 run
- ✅ Wallet: $50.00
- ✅ Quick actions work

### **2. Chain Builder** (`/chains`) **[AGENT LIBRARY HERE]**
- ✅ Agent Library panel on right
- ✅ Shows "Available Agents (6)"
- ✅ **Refresh Agents button**
- ✅ Auto-refreshes every 5 seconds
- ✅ Search filters agents
- ✅ Can drag to canvas

### **3. Run History** (`/runs`)
- ✅ Shows 1 executed run
- ✅ Timeline: Started 2025-11-01T16:27:53
- ✅ Timeline: Completed 2025-11-01T16:27:54
- ✅ Duration: 1.0s
- ✅ No "None" values

### **4. Code Fuser** (`/code-fuser`)
- ✅ Dropdown shows 6 agents
- ✅ Generate Python code
- ✅ Generate JavaScript code
- ✅ Generate cURL commands

### **5. Marketplace** (`/marketplace`)
- ✅ All 6 agents displayed
- ✅ Prices: 20¢ - 65¢
- ✅ Search works
- ✅ Filter by category

### **6. My Agents** (`/agents`)
- ✅ List all agents
- ✅ Create new agent
- ✅ Delete agents
- ✅ View details

---

## 🔄 HOW AGENT LIBRARY REFRESH WORKS

The Chain Builder agent library has **4 refresh mechanisms**:

| Mechanism | Trigger | Speed | Description |
|-----------|---------|-------|-------------|
| **Auto-refresh** | Every 5 seconds | Automatic | Runs in background |
| **Focus trigger** | Switch to tab | Immediate | When tab gains focus |
| **Visibility trigger** | Page visible | Immediate | When navigating back |
| **Manual button** | Click refresh | Immediate | Shows agent count |

**This means new agents will appear within 5 seconds maximum, or immediately if you:**
- Switch browser tabs
- Click the refresh button
- Navigate back to Chain Builder

---

## 🧪 VERIFICATION COMMANDS

```bash
# Check if services are running
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/QUICK_VERIFY.py

# Test complete system
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/COMPLETE_SYSTEM_TEST.py

# Test agent refresh specifically
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/TEST_AGENT_REFRESH.py

# Check backend health
curl http://localhost:8000/health

# Check agent count
curl http://localhost:8000/api/agents | python3 -c "import sys, json; print(f'Agents: {len(json.load(sys.stdin))}')"

# Check frontend
curl -I http://localhost:3000
```

---

## 🛑 STOP THE APPLICATION

```bash
# Stop both services
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

---

## 📊 TROUBLESHOOTING

### **Problem: Agent library shows 0 agents**

**Solution:**
1. Check backend has agents:
   ```bash
   curl http://localhost:8000/api/agents
   ```
2. If empty, create agents using the test script
3. Click "Refresh Agents" button
4. Hard refresh browser

### **Problem: Agents not updating after creation**

**Solution:**
1. **Wait 5 seconds** - auto-refresh will trigger
2. **Click "Refresh Agents"** button manually
3. **Switch tabs** - switch away and back
4. Check browser console (F12) for errors

### **Problem: Blank page**

**Solution:**
1. Hard refresh: `Cmd+Shift+R` or `Ctrl+Shift+R`
2. Clear browser cache
3. Check console (F12) for errors
4. Restart frontend:
   ```bash
   lsof -ti:3000 | xargs kill -9
   cd frontend && npm run dev
   ```

### **Problem: Services won't start**

**Solution:**
```bash
# Kill everything and restart
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
sleep 2
/Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh
```

---

## 📋 QUICK REFERENCE

### **URLs:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### **Credentials:**
- Username: `demo`
- Password: `demo123`

### **Key Files:**
- Backend: `/Users/abdulmuiz/Documents/LAB/Gptgram/backend/test_server.py`
- Frontend: `/Users/abdulmuiz/Documents/LAB/Gptgram/frontend`
- Startup Script: `/Users/abdulmuiz/Documents/LAB/Gptgram/RUN_APPLICATION.sh`

### **Logs:**
- Backend: `/tmp/gptgram_backend.log`
- Frontend: `/tmp/gptgram_frontend.log`

### **Test Scripts:**
- Quick Verify: `QUICK_VERIFY.py`
- Complete Test: `COMPLETE_SYSTEM_TEST.py`
- Agent Refresh: `TEST_AGENT_REFRESH.py`

---

## ✅ COMPLETE VERIFICATION CHECKLIST

After starting the application, verify:

- [ ] Backend running (http://localhost:8000/health)
- [ ] Frontend running (http://localhost:3000)
- [ ] Can login with demo/demo123
- [ ] Dashboard shows 6 agents
- [ ] Chain Builder loads
- [ ] Agent Library shows "Available Agents (6)"
- [ ] Refresh Agents button works
- [ ] Can click an agent to see details
- [ ] Can drag agent to canvas
- [ ] Run History shows 1 run
- [ ] Timeline has real timestamps (no "None")
- [ ] Code Fuser dropdown shows 6 agents
- [ ] Marketplace shows all agents
- [ ] Can create new agent
- [ ] New agent appears in Chain Builder within 5 seconds

---

## 🎉 YOU'RE READY!

The application is fully configured with:
- ✅ 6 diverse agents ready to use
- ✅ Agent library auto-refresh working
- ✅ Timeline tracking with no "None" values
- ✅ Code Fuser generating integration code
- ✅ Complete marketplace functionality
- ✅ Run history with detailed outputs

**Start building agent chains at http://localhost:3000!**

---

## 📝 NEXT STEPS

1. **Open the application:**
   ```
   http://localhost:3000
   ```

2. **Login:**
   ```
   demo / demo123
   ```

3. **Go to Chain Builder:**
   ```
   /chains
   ```

4. **Verify Agent Library:**
   - Right panel shows 6 agents
   - Refresh button shows count
   - Auto-updates every 5 seconds

5. **Build a chain:**
   - Add Input Node
   - Drag agents from library
   - Connect them
   - Click "Run Chain"

6. **Check results:**
   - Go to Run History
   - See timeline
   - Expand for outputs

**Happy building!** 🚀
