# 🧪 GPTGRAM COMPLETE TESTING GUIDE

## Comprehensive Testing Documentation for Full Platform

Based on all discussions, fixes, and requirements from the conversation history.

---

# TABLE OF CONTENTS

1. [Backend API Tests](#1-backend-api-tests)
2. [Frontend UI Tests](#2-frontend-ui-tests)
3. [Agent System Tests](#3-agent-system-tests)
4. [Chain Builder Tests](#4-chain-builder-tests) ⭐ CRITICAL
5. [Timeline & Execution Tests](#5-timeline--execution-tests) ⭐ FIXED
6. [Wallet & Money Tests](#6-wallet--money-tests)
7. [Code Fuser Tests](#7-code-fuser-tests) ⭐ FIXED
8. [Integration Tests](#8-integration-tests)
9. [Automated Test Scripts](#9-automated-test-scripts)
10. [Performance & Security](#10-performance--security-tests)

---

# 1. BACKEND API TESTS

## 1.1 Health & Status

```bash
# Test: Backend Health
curl http://localhost:8000/health

✓ Status 200
✓ Response: {"status":"healthy","timestamp":"..."}
✓ Response time < 100ms
```

## 1.2 Agent Management APIs

### List Agents
```bash
GET /api/agents

✓ Returns array of agents
✓ Each has: id, name, type, endpoint_url, price_cents
✓ IDs are unique UUIDs
✓ Prices are non-negative integers
✓ Timestamps in ISO 8601 format
```

### Create Agent
```bash
POST /api/agents
{
  "name": "Test Agent",
  "type": "custom",
  "endpoint_url": "http://test.com",
  "price_cents": 50,
  "verification_level": "L2"
}

✓ Status 200/201
✓ Returns created agent with ID
✓ HMAC secret NOT returned
✓ created_at timestamp added
✓ Agent appears in GET list
```

### Update Agent
```bash
PUT /api/agents/{id}

✓ Status 200
✓ Updated fields changed
✓ Non-updated fields preserved
✓ updated_at timestamp modified
```

### Delete Agent
```bash
DELETE /api/agents/{id}

✓ Status 200/204
✓ Agent removed from list
✓ GET returns 404
✓ Related data handled properly
```

### Execute Agent
```bash
POST /api/agents/{id}/execute
{"text": "test input"}

✓ Status 200
✓ Returns output object
✓ No hanging (timeout < 30s)
✓ Cost deducted from wallet
✓ Error handling for invalid input
```

## 1.3 Chain Execution APIs

### Create Run ⭐ CRITICAL - Timeline Fix
```bash
POST /api/runs/create
{
  "chain_id": "test_001",
  "status": "running",
  "nodes": ["input", "agent1", "agent2"]
}

✓ Status 200/201
✓ run_id generated (UUID)
✓ started_at timestamp SET
✓ started_at is NOT "None" ⭐
✓ started_at in ISO 8601 format
✓ started_at timezone-aware (+00:00 or Z)
✓ Includes microseconds
```

### Update Run (Complete) ⭐ CRITICAL
```bash
PUT /api/runs/{id}
{
  "status": "completed",
  "outputs": {...},
  "total_cost": 150
}

✓ Status 200
✓ completed_at timestamp SET
✓ completed_at is NOT "None" ⭐
✓ completed_at > started_at
✓ Duration calculable
✓ Outputs stored
✓ Cost recorded
```

### List Runs - Timeline Verification ⭐
```bash
GET /api/runs/

✓ Returns array of runs
✓ NO "None" in started_at ⭐
✓ NO "None" in completed_at ⭐
✓ All timestamps ISO 8601
✓ Completed runs have both timestamps
✓ Can calculate duration for each
```

## 1.4 Wallet APIs

### Get Balance
```bash
GET /api/wallet/balance

✓ Status 200
✓ Balance is integer (cents)
✓ Balance >= 0
✓ Formatted amount correct
```

### Top-up
```bash
POST /api/wallet/topup
{"amount": 1000}

✓ Balance increases
✓ Transaction recorded
✓ Negative amounts rejected (400)
```

---

# 2. FRONTEND UI TESTS

## 2.1 Authentication

### Login Page
```
1. Navigate to http://localhost:3000
2. Should redirect to /login if not authenticated

✓ Login form visible
✓ Username and password fields
✓ Sign In button
✓ No console errors
```

### Login Success
```
Username: demo
Password: demo123

✓ Login request succeeds
✓ Token stored
✓ Redirected to /
✓ Navigation appears
```

### Login Failure
```
Wrong credentials

✓ Error message shown
✓ Stays on login page
✓ Can retry
```

## 2.2 Dashboard

### Dashboard Load
```
URL: /

✓ Title: "Dashboard"
✓ Stats cards load
✓ Agent count matches API
✓ Run count matches API
✓ Wallet balance displayed ($XX.XX)
✓ Recent activity shown
✓ Quick action buttons work
```

## 2.3 Navigation

### Sidebar
```
✓ All links visible:
  - Dashboard (/)
  - Marketplace (/marketplace)
  - My Agents (/agents)
  - Chain Builder (/chains) ⭐
  - Run History (/runs) ⭐
  - Code Fuser (/code-fuser) ⭐
  - Wallet (/wallet)
✓ Active route highlighted
✓ Clicks navigate correctly
✓ Icons display
```

---

# 3. AGENT SYSTEM TESTS

## 3.1 Agent Library

### View Agents
```
URL: /agents

✓ Grid/list of agents
✓ Each card shows: name, description, price, category
✓ Search box functional
✓ Filter by category works
✓ Sort options work
✓ Empty state if no agents
```

## 3.2 Create Agent

### Form Validation
```
✓ Name: required, 3-100 chars
✓ Description: required, 10-500 chars
✓ Endpoint URL: required, valid URL format
✓ Price: required, >= 0, integer
✓ Verification Level: required, L1/L2/L3
✓ HMAC Secret: optional, min 8 chars if provided
```

### Create Success
```
✓ Form validates
✓ POST to /api/agents
✓ Success message
✓ Redirect to agent list
✓ New agent appears
✓ Agent count increases
```

## 3.3 Edit Agent

```
✓ Form pre-filled with current data
✓ Can modify fields
✓ Validation same as create
✓ PUT request on save
✓ Changes reflect immediately
```

## 3.4 Delete Agent

```
✓ Confirmation dialog appears
✓ Shows agent details
✓ Warning message
✓ DELETE request on confirm
✓ Agent removed from list
✓ Count decreases
```

## 3.5 Execute Agent

```
✓ Input form based on schema
✓ Execute button triggers POST
✓ Loading state shown
✓ Output displayed
✓ Cost deducted
✓ Error handling for failures
```

---

# 4. CHAIN BUILDER TESTS ⭐ CRITICAL

## 4.1 Canvas Load

```
URL: /chains

✓ React Flow canvas renders
✓ Agent library panel (right side)
✓ Toolbar visible
✓ No console errors
✓ Pan and zoom work
```

## 4.2 Agent Library Panel ⭐ MAIN FIX

### Display
```
✓ Title: "Agent Library" or "Available Agents"
✓ Shows count: "Available Agents (X)"
✓ Search box at top
✓ Refresh button: "Refresh Agents (X)"
✓ Scrollable list of agents
✓ Each agent shows: name, category, price, description
```

### Auto-Refresh ⭐ CRITICAL FIX
```
Test: Create new agent, return to chain builder

Expected:
✓ Agent count updates automatically within 5 seconds
✓ New agent appears in library
✓ No manual action needed
✓ Console logs: "Loaded agents: X agents"

Triggers:
✓ Auto-refresh: Every 5 seconds (setInterval)
✓ Focus trigger: Switch tab and back (focus event)
✓ Visibility trigger: Page becomes visible (visibilitychange event)
✓ Manual button: Click "Refresh Agents"
```

### Manual Refresh Button ⭐ CRITICAL
```
Steps:
1. Click "Refresh Agents (X)" button

Expected:
✓ Loading state briefly shown
✓ API call to /api/agents
✓ List updates
✓ Alert shows:
  - "Found X new agent(s)" if increased
  - "Total: X agents" if same
✓ Button count updates
✓ No errors
```

### Search Functionality
```
✓ Real-time filtering
✓ Searches: name, description, type, category
✓ Case-insensitive
✓ Count updates
✓ Clear button appears
✓ Empty state if no matches
```

## 4.3 Adding Nodes

### Add Input Node
```
✓ Button adds input node to canvas
✓ Node has input icon and label
✓ Editable text field
✓ Output handle visible
✓ Node movable
✓ Position saved
```

### Drag Agent from Library
```
✓ Agent card is draggable
✓ Drag indicator appears
✓ Drop on canvas creates agent node
✓ Node shows agent name, icon
✓ Input and output handles visible
✓ Node contains agent metadata
```

### Add Moderator Node
```
✓ Button adds moderator node
✓ Distinct styling from agents
✓ Moderator icon
✓ Editable fields
✓ Correct connection logic
```

## 4.4 Connecting Nodes

### Create Connections
```
✓ Drag from output handle to input handle
✓ Connection line appears
✓ Animated flow direction
✓ Connection stored in state
✓ Can connect multiple nodes in sequence
```

### Connection Validation
```
✓ Prevent invalid connections
✓ No cycles (feedback loops)
✓ Input can have only one incoming edge
✓ Output can have multiple outgoing edges
✓ Error message for invalid attempts
```

### Delete Connections
```
✓ Click connection to select
✓ Press Delete or click X
✓ Connection removed
✓ Nodes remain
```

## 4.5 Run Chain

### Execute Chain
```
✓ "Run Chain" button visible
✓ Button disabled if no valid chain
✓ Click triggers execution
✓ Loading state shown
✓ POST to /api/runs/create
✓ Chain executes node by node
✓ Progress shown (if applicable)
✓ Success dialog on completion
```

### Execution Results
```
✓ Show run ID
✓ Display outputs for each node
✓ Show total cost
✓ Show execution time
✓ Link to run history
✓ Option to run again
```

### Execution Errors
```
✓ Network errors handled
✓ Agent failures shown
✓ Insufficient balance error
✓ Timeout errors caught
✓ User-friendly error messages
```

## 4.6 Save/Load Chain

### Save Chain
```
✓ "Save Chain" button
✓ Prompt for chain name
✓ Save nodes and connections
✓ Confirmation message
```

### Load Chain
```
✓ "Load Chain" dropdown
✓ List of saved chains
✓ Select chain loads to canvas
✓ All nodes and connections restored
```

---

# 5. TIMELINE & EXECUTION TESTS ⭐ FIXED

## 5.1 Run History Page

### Page Load
```
URL: /runs

✓ Title: "Run History"
✓ List of runs displayed
✓ Filter buttons: All, Succeeded, Failed, Running
✓ Refresh button
✓ No console errors
```

## 5.2 Run Timeline Display ⭐ CRITICAL FIX

### Timeline Information
```
For each run:
✓ Started timestamp DISPLAYED
✓ Started is NOT "None" ⭐
✓ Started format: "2025-11-08T15:30:00"
✓ Completed timestamp DISPLAYED (if completed)
✓ Completed is NOT "None" ⭐
✓ Duration calculated and shown
✓ Duration format: "1.5s" or "250ms"
```

### Timestamp Verification ⭐ MAIN FIX
```
Critical Checks:
✓ No "None" text anywhere in timeline
✓ All timestamps are real dates
✓ Timestamps in human-readable format
✓ Fallback to "N/A" if truly missing (not "None")
✓ Duration > 0 for completed runs
✓ Completed > Started always
```

## 5.3 Run Details

### Expand Run
```
✓ Click run card to expand
✓ Shows full timeline
✓ Shows node execution details
✓ Shows input/output for each node
✓ Shows cost breakdown
✓ Shows error details if failed
```

### Node-Level Timeline
```
✓ Each node shows execution time
✓ Node status indicators
✓ Sequential execution order clear
✓ Failed node highlighted
```

## 5.4 Filter & Search Runs

```
✓ Filter by status works
✓ Filter by date range (if available)
✓ Search by chain name
✓ Count badges update
✓ Empty state for no results
```

---

# 6. WALLET & MONEY TESTS

## 6.1 Wallet Display

### Balance
```
URL: /wallet

✓ Current balance shown
✓ Format: $XX.XX
✓ Matches API /api/wallet/balance
✓ Updates in real-time
✓ No negative values
```

## 6.2 Top-up

### Top-up Options
```
✓ Multiple amount options ($10, $25, $50, $100)
✓ Custom amount input
✓ Payment method selection (mock or real)
✓ Clear pricing
```

### Top-up Process
```
✓ Select amount
✓ Click top-up button
✓ Payment dialog/redirect
✓ POST to /api/wallet/topup
✓ Balance increases immediately
✓ Success notification
✓ Transaction appears in history
```

## 6.3 Transaction History

```
✓ List of all transactions
✓ Each shows: date, type, amount, balance after
✓ Types: top-up, chain execution, refund
✓ Sorted by date (newest first)
✓ Pagination if many transactions
```

## 6.4 Cost Tracking

### Chain Execution Cost
```
✓ Cost preview before execution
✓ Cost calculated from agent prices
✓ Balance check before execution
✓ Insufficient funds prevents execution
✓ Actual cost deducted after execution
✓ Cost matches estimate
```

### Agent Pricing
```
✓ Agent price displayed consistently
✓ Price in cents internally, formatted for display
✓ Price can be updated
✓ Price changes don't affect past runs
```

---

# 7. CODE FUSER TESTS ⭐ FIXED

## 7.1 Code Fuser Page

### Page Load
```
URL: /code-fuser

✓ Title: "Code Fuser"
✓ Agent dropdown populated
✓ Language tabs: Python, JavaScript, cURL
✓ Code editor/display area
✓ Generate button
✓ Copy and Download buttons
```

## 7.2 Agent Selection ⭐ CRITICAL FIX

### Dropdown Population
```
✓ Dropdown shows ALL agents from API
✓ Agent count matches /api/agents
✓ Each option shows: agent name, price
✓ Placeholder: "Select an agent"
✓ Alphabetically sorted or by category
```

### Auto-Update
```
✓ Dropdown refreshes when new agents added
✓ No need to reload page
✓ New agents appear in dropdown
```

## 7.3 Code Generation

### Python Code
```
Steps:
1. Select agent
2. Select "Python" tab
3. Click "Generate Code"

Expected:
✓ Python integration code generated
✓ Includes: class definition, execute method
✓ Shows agent ID, endpoint, HMAC secret
✓ Includes example usage
✓ Proper Python syntax
✓ Imports listed
✓ Code is copy-pasteable and runnable
```

### JavaScript Code
```
Expected:
✓ JavaScript/Node.js code generated
✓ Uses axios or fetch
✓ Includes HMAC signature logic
✓ Proper JS syntax
✓ ESM or CommonJS format
✓ Example usage included
```

### cURL Command
```
Expected:
✓ Complete cURL command
✓ Includes headers (Content-Type, X-GPTGRAM-Signature)
✓ Includes JSON payload
✓ Endpoint URL correct
✓ Ready to run in terminal
```

## 7.4 Code Actions

### Copy Code
```
✓ "Copy" button copies to clipboard
✓ Success notification
✓ Button changes to "Copied!" briefly
✓ Works in all browsers
```

### Download Code
```
✓ "Download" button downloads file
✓ Filename: agent-name-integration.py (or .js)
✓ File contains generated code
✓ File is properly formatted
```

## 7.5 Multi-Agent Support ⭐ GENERALIZED

```
✓ Works with ANY agent in system
✓ Code adapts to agent properties
✓ No hardcoded agent IDs
✓ Dynamically loads agent list
✓ Supports all agent types
```

---

# 8. INTEGRATION TESTS

## 8.1 End-to-End Workflow

### Complete Agent Chain Workflow
```
Test Steps:
1. Create 3 new agents via /agents
2. Go to /chains
3. Verify all 3 agents in library (auto-refresh check)
4. Build chain: Input → Agent1 → Agent2 → Agent3
5. Add input text
6. Execute chain
7. Wait for completion
8. Go to /runs
9. Verify run appears with timeline
10. Check timeline has NO "None" values
11. Verify all outputs present
12. Check wallet balance decreased
13. Go to /code-fuser
14. Verify all 3 agents in dropdown
15. Generate code for one agent

Expected:
✓ All steps complete without errors
✓ Data persists across pages
✓ Timeline shows real dates
✓ Wallet updated correctly
✓ All features interconnected
```

## 8.2 Real-Time Updates

### Cross-Page Updates
```
Test:
1. Open two browser tabs
2. Tab 1: /chains (agent library)
3. Tab 2: /agents (create agent)
4. Create agent in Tab 2
5. Switch to Tab 1

Expected:
✓ Tab 1 shows new agent within 5 seconds
✓ Or immediately on tab switch
✓ Count updated
```

## 8.3 State Persistence

### Refresh Behavior
```
Test:
1. Build complex chain
2. Hard refresh browser (Cmd+Shift+R)
3. Check if chain still visible

Expected:
✓ Chain preserved (if saved)
✓ Or warning about unsaved changes
✓ No data loss
```

---

# 9. AUTOMATED TEST SCRIPTS

## 9.1 Quick Verification

```bash
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/QUICK_VERIFY.py

Checks:
✓ Backend running
✓ Frontend running
✓ Agent count
✓ Run count
✓ Displays summary
```

## 9.2 Complete System Test

```bash
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/COMPLETE_SYSTEM_TEST.py

Actions:
✓ Clears existing agents
✓ Creates 6 diverse agents
✓ Tests agent execution
✓ Creates 4-node chain
✓ Executes chain
✓ Verifies timeline (no "None")
✓ Checks all features
✓ Provides browser test instructions
```

## 9.3 Agent Refresh Test

```bash
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/TEST_AGENT_REFRESH.py

Actions:
✓ Counts initial agents
✓ Creates new test agent
✓ Verifies in API
✓ Tests execution
✓ Provides browser verification steps
```

## 9.4 Selenium Browser Test

```bash
python3 /Users/abdulmuiz/Documents/LAB/Gptgram/SELENIUM_TEST.py

Automated Browser Tests:
✓ Opens Chrome
✓ Navigates to /login
✓ Logs in
✓ Tests dashboard
✓ Tests chain builder
✓ Tests run history
✓ Tests code fuser
✓ Tests marketplace
✓ Tests wallet
✓ Tests navigation
✓ Generates report
```

---

# 10. PERFORMANCE & SECURITY TESTS

## 10.1 Performance

### Load Time
```
✓ Initial page load < 3s
✓ Navigation between pages < 1s
✓ API responses < 500ms
✓ Large agent list renders without lag
✓ Complex chains execute in reasonable time
```

### Responsiveness
```
✓ UI responsive on desktop
✓ UI responsive on tablet
✓ UI responsive on mobile
✓ Canvas works on touch devices
```

## 10.2 Security

### Authentication
```
✓ Protected routes redirect to login
✓ Token expiration handled
✓ Logout clears session
✓ No sensitive data in localStorage/cookies
```

### API Security
```
✓ HMAC validation for agent execution
✓ CORS configured correctly
✓ No SQL injection vulnerabilities
✓ Rate limiting (if implemented)
✓ Input validation on all endpoints
```

### Data Safety
```
✓ HMAC secrets never exposed in frontend
✓ Wallet balance can't be manipulated client-side
✓ Agent endpoints validated
✓ XSS prevention in user inputs
```

---

# TEST EXECUTION CHECKLIST

## Pre-Testing
- [ ] Backend running (port 8000)
- [ ] Frontend running (port 3000)
- [ ] Database/storage cleared (for clean test)
- [ ] Browser cache cleared
- [ ] Console open (F12) to monitor errors

## Critical Tests ⭐
- [ ] Agent library auto-refresh (5-second interval)
- [ ] Agent library manual refresh button
- [ ] Timeline shows real dates (NO "None" values)
- [ ] Duration calculated correctly
- [ ] Code Fuser dropdown shows all agents
- [ ] Code Fuser generates correct code
- [ ] Wallet balance updates after chain execution
- [ ] Complex chain (4+ nodes) executes successfully

## All Features
- [ ] Login/logout
- [ ] Dashboard statistics
- [ ] Create agent
- [ ] Edit agent
- [ ] Delete agent
- [ ] Execute single agent
- [ ] Build chain (drag & drop)
- [ ] Connect nodes
- [ ] Execute chain
- [ ] View run history
- [ ] Expand run details
- [ ] Filter runs
- [ ] Generate integration code
- [ ] Copy/download code
- [ ] View marketplace
- [ ] Search/filter agents
- [ ] Top-up wallet
- [ ] View transaction history

## Automated Tests
- [ ] Run QUICK_VERIFY.py
- [ ] Run COMPLETE_SYSTEM_TEST.py
- [ ] Run TEST_AGENT_REFRESH.py
- [ ] Run SELENIUM_TEST.py (if available)

## Browser Testing
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Final Verification
- [ ] No console errors
- [ ] No "None" in UI
- [ ] All timestamps formatted
- [ ] All prices formatted
- [ ] All APIs responding
- [ ] All buttons functional
- [ ] All links working
- [ ] Responsive on mobile

---

# TEST RESULTS TEMPLATE

```
Date: ___________
Tester: ___________
Environment: Development / Staging / Production

Backend Status: ✓ Running / ✗ Down
Frontend Status: ✓ Running / ✗ Down

Critical Issues Found: ___________

Total Tests Run: ___________
Tests Passed: ___________
Tests Failed: ___________
Tests Skipped: ___________

Pass Rate: _______%

Critical Bugs:
1. 
2. 
3. 

Minor Bugs:
1. 
2. 
3. 

Recommendations:
1. 
2. 
3. 

Sign-off: ___________
```

---

# KNOWN FIXES APPLIED

Based on conversation history:

1. **CompleteRuns.jsx syntax error** - FIXED
   - Created CompleteRunsFixed.jsx
   - Proper JSX structure
   - No more blank page

2. **Timeline "None" values** - FIXED
   - Backend sets timezone-aware timestamps
   - Frontend checks for "None" and handles gracefully
   - Fallback to current time if missing
   - Duration calculation working

3. **Agent library not updating** - FIXED
   - Auto-refresh every 5 seconds
   - Focus trigger on tab switch
   - Visibility trigger on page visible
   - Manual refresh button with feedback

4. **Code Fuser not generalized** - FIXED
   - Created CodeFuserWorking.jsx
   - Dynamically loads all agents
   - Works with any agent
   - Multiple language support

---

**END OF TESTING GUIDE**

For any issues, refer to:
- COMPLETE_GUIDE.md
- HOW_TO_RUN.md
- AGENT_LIBRARY_REFRESH_FIXED.md
- READY_TO_USE.md
