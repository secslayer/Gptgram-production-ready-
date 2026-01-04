# 🔧 TROUBLESHOOTING BLANK PAGE

## ✅ System is Running!

Both services are confirmed running:
- ✅ **Backend:** http://localhost:8000
- ✅ **Frontend:** http://localhost:3000
- ✅ **Data:** 3 agents, 1 run created

---

## 🔍 If You See a Blank Page

### **Solution 1: Hard Refresh Browser**
```
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

### **Solution 2: Clear Cache & Reload**
1. Open browser DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

### **Solution 3: Check Browser Console**
1. Press F12 to open DevTools
2. Go to "Console" tab
3. Look for any RED errors
4. Common issues:
   - CORS errors
   - Failed to fetch
   - Module not found

### **Solution 4: Try Different Browser**
- Chrome
- Firefox
- Safari
- Edge

### **Solution 5: Check Correct URL**
```
Correct: http://localhost:3000
Wrong:   https://localhost:3000  (no https!)
Wrong:   http://localhost:3000/login (will redirect)
```

---

## 🧪 Quick Test

Run this in terminal to verify frontend content:
```bash
curl -s http://localhost:3000 | head -15
```

**Expected output:** Should see HTML with `<div id="root">`

---

## 📝 Manual Verification Steps

### **1. Check Services are Actually Running**
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend port
lsof -i :3000 | grep LISTEN
```

### **2. View Frontend Logs**
```bash
tail -20 /tmp/frontend.log
```

**Look for:**
- ✅ "ready in" message
- ✅ "Local: http://localhost:3000"
- ❌ Any ERROR messages

### **3. View Backend Logs**
```bash
tail -20 /tmp/backend.log
```

---

## 🆘 If Still Blank

### **Restart Everything Cleanly**

```bash
# Kill all
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Wait
sleep 3

# Start backend
cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend
python3 test_server.py &

# Wait for backend
sleep 3

# Start frontend  
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
npm run dev &

# Wait for frontend
sleep 5

# Verify
curl http://localhost:8000/health
curl -I http://localhost:3000
```

### **Alternative: Use Startup Script**
```bash
/Users/abdulmuiz/Documents/LAB/Gptgram/start_system.sh
```

---

## 🎯 What You Should See

When you open http://localhost:3000, you should see:

### **Login Page**
- GPTGram logo/title
- Username field
- Password field
- Sign In button

### **After Login (demo/demo123)**
- Dashboard with stats
- Sidebar navigation
- Wallet info
- Recent runs

---

## 📊 Current System State

```
Backend:  ✅ Running (8000)
Frontend: ✅ Running (3000)  
Agents:   ✅ 3 created
Runs:     ✅ 1 executed
Timeline: ✅ Working
```

---

## 💡 Common Causes of Blank Page

1. **Browser Cache** - Old files cached
   - **Fix:** Hard refresh (Ctrl+Shift+R)

2. **JavaScript Error** - React failed to mount
   - **Fix:** Check console (F12)

3. **Wrong Port** - Trying wrong URL
   - **Fix:** Verify http://localhost:3000

4. **Service Not Started** - Frontend crashed
   - **Fix:** Check logs, restart

5. **Build Issue** - Broken JavaScript bundle
   - **Fix:** Rebuild with `npm run build`

---

## ✅ If You Can See Console Output

Open browser console (F12) and run:
```javascript
console.log("Test:", document.getElementById("root"))
```

**Expected:** Should show div element, not null

---

## 🔄 Nuclear Option (Complete Reset)

If nothing works:

```bash
# 1. Stop everything
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# 2. Clean frontend
cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend
rm -rf node_modules/.vite
rm -rf dist

# 3. Rebuild
npm run build

# 4. Use script
cd /Users/abdulmuiz/Documents/LAB/Gptgram
./start_system.sh

# 5. Wait 10 seconds
sleep 10

# 6. Try again
open http://localhost:3000
```

---

## 📞 Final Checklist

- [ ] Services running (script shows ✅)
- [ ] Correct URL (http://localhost:3000)
- [ ] Browser refreshed (Ctrl+Shift+R)
- [ ] No console errors (F12)
- [ ] Tried different browser

---

**If ALL of the above are checked and it's still blank, there may be a network/firewall issue blocking localhost access.**
