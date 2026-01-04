# ✅ GPTGRAM BROWSER TEST CHECKLIST

## 🚀 System is Running!

**Backend:** http://localhost:8000 ✅  
**Frontend:** http://localhost:3000 ✅

---

## 📝 Quick Test Steps

### 1. **Open Browser**
- Go to: http://localhost:3000
- You should see the **login page** (not blank)

### 2. **Login**
- Username: `demo`
- Password: `demo123`
- Click "Sign In"

### 3. **Test Each Page**

#### **Dashboard** (/)
- [ ] Shows wallet balance: $50.00
- [ ] Shows agent count: 2
- [ ] Shows run count: 0
- [ ] Quick action buttons work

#### **Marketplace** (/marketplace)
- [ ] Click "Marketplace" in sidebar
- [ ] Shows 2 agents (Test Summarizer, Test Sentiment)
- [ ] Prices displayed (50¢, 30¢)
- [ ] Search box works
- [ ] Install buttons visible

#### **My Agents** (/agents)
- [ ] Shows 2 agents in list
- [ ] Create Agent button works
- [ ] Delete buttons visible
- [ ] Agent details shown

#### **Chain Builder** (/chains)
- [ ] Agent Library panel on right
- [ ] Shows "Available Agents (2)"
- [ ] Test Summarizer - 50¢
- [ ] Test Sentiment - 30¢
- [ ] Can drag agents to canvas
- [ ] Search box filters agents

#### **Run History** (/runs)
- [ ] Shows "No runs found" (initially)
- [ ] Refresh button works
- [ ] No "None" values in UI

---

## 🧪 Test Complex Chain

1. Go to **Chain Builder**
2. Click **"Add Input Node"**
3. Double-click input node and add text: "Hello world"
4. Click **Test Summarizer** from library
5. Connect Input → Test Summarizer
6. Click **"Run Chain"** button
7. Wait for success dialog
8. Go to **Run History**
9. Verify:
   - Run appears with timestamp
   - Started: 2025-11-01T15:XX:XX
   - Status: Completed
   - Can expand to see outputs

---

## ✅ If Everything Works

You should be able to:
- Navigate all pages without errors
- See agents in library
- Build and execute chains
- View run history with proper timestamps

---

## ❌ If Issues

### Blank Page?
```bash
# Check console (F12 in browser) for errors
# Restart frontend:
lsof -ti:3000 | xargs kill -9
cd frontend && npx vite preview --port 3000
```

### Agents Not Showing?
```bash
# Check backend:
curl http://localhost:8000/api/agents
# Should return JSON with 2 agents
```

### Can't Login?
- Use: demo / demo123
- Check backend is running:
```bash
curl http://localhost:8000/health
```

---

## 🎯 Current System State

| Component | Status | Details |
|-----------|--------|---------|
| Backend | ✅ Running | Port 8000 |
| Frontend | ✅ Running | Port 3000 |
| Agents | ✅ 2 Created | Test Summarizer, Test Sentiment |
| Database | ✅ Working | In-memory |
| Auth | ✅ Working | demo/demo123 |

**Everything should be working now!** 🚀
