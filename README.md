# GPTGram - A2A DAG Orchestration Platform

## Executive Summary
GPTGram is an Agent-to-Agent (A2A) marketplace and DAG orchestration platform that lets users compose, verify, price and run multi-agent workflows with deterministic mapping first, a GAT-powered recommendation layer, and strict LLM fallback controls - built for reliability, traceability, and monetizable trust.

## Key Features
- **A2A Compliant**: Full adherence to Google A2A protocol for agent interoperability
- **n8n Compatible**: Native support for n8n webhook agents with HMAC verification
- **DAG Orchestration**: Execute complex branching and merging workflows
- **Smart Transform Pipeline**: Deterministic → GAT → LLM fallback hierarchy
- **Graph Attention Network**: AI-powered agent recommendations and mapping suggestions
- **Provenance Tracking**: Complete per-field lineage and confidence scoring
- **Idempotent Payments**: Secure wallet system with hold/settle/refund flows
- **Gemini LLM Integration**: Connected to Gemini API for intelligent fallbacks

## 🎯 Investor Demo UI Wireframe Checklist

### ✅ Dashboard (Landing View)
- [x] **Wallet Balance Widget** - Shows current balance with 1-click top-up
- [x] **Quick Action Cards** - Create Agent, Build Chain, View Runs, Top Up
- [x] **Key Metrics Grid** - Total Agents, Chains, Success Rate, Active Runs
- [x] **Recent Runs Panel** - Live status with cost burn meters
- [x] **Performance Stats** - Success rates, total spent, active runs

### ✅ Chain Builder Canvas
- [x] **Drag & Drop Interface** - Visual DAG builder with React Flow
- [x] **Agent Library Sidebar** - Searchable list with verification badges
- [x] **Compatibility Edges** - Color-coded edges showing compatibility scores (%)
- [x] **Node Inspector Panel** - Click node to see schema, price, verification
- [x] **Live Cost Estimator** - Real-time total cost calculation
- [x] **Run Controls** - Run button with progress indicator
- [x] **Result Panel** - Shows output JSON with provenance hover

### ✅ Agent Management
- [x] **Agent Cards Grid** - Shows verification level (L1/L2/L3), price, type
- [x] **Verification Status Badges** - Green (L3), Yellow (L2), Orange (L1), Red (Unverified)
- [x] **Performance Metrics** - Success rate, avg latency, call volume
- [x] **Quick Actions** - Test, Verify, Use buttons on each card
- [x] **Agent Detail Modal** - Full schema view, metrics, endpoint info

### ✅ Run History & Provenance
- [x] **Execution Timeline** - Step-by-step node execution with timing
- [x] **Cost Breakdown** - Per-node cost and total spent
- [x] **Transform Method Badges** - Shows Deterministic/GAT/LLM for each transform
- [x] **Provenance Viewer** - Expandable per-field origin tracking
- [x] **Confidence Scores** - Percentage confidence for each field
- [x] **Export Options** - Download provenance report

### ✅ Analytics Dashboard
- [x] **Revenue Metrics** - Total revenue, daily trends, cost breakdown pie chart
- [x] **Agent Performance** - Bar charts showing most-used agents
- [x] **Transform Analytics** - Success rates by method (Deterministic > GAT > LLM)
- [x] **GAT Performance** - Inference time, successful mappings, cost savings

### ✅ Live Demo Features
- [x] **Real-time Updates** - WebSocket updates for running chains
- [x] **Progress Indicators** - Animated node execution during runs
- [x] **Error Handling** - Clear error messages with remediation suggestions
- [x] **Wallet Transactions** - Live balance updates during execution

## 90-Second Investor Demo Script

### 0-10s: Show Wallet & Quick Setup
- Show wallet balance of $50.00
- Click "Top Up" to add $10 (instant update to $60.00)
- "Ready to build intelligent agent workflows"

### 10-30s: Create n8n Agent
- Click "Create Agent" 
- Name: "n8n Summarizer"
- Type: n8n webhook
- Show auto-verification running (3 tests)
- Badge changes to "L2 Verified" ✓

### 30-60s: Build 3-Node Chain
1. Drag **Summarizer** (L2, $0.50) to canvas
2. Drag **Sentiment Analyzer** (L3, $0.30) 
3. Drag **Translator** (L2, $0.75)
4. Connect nodes - edges show compatibility:
   - Summarizer → Sentiment: 87% (green)
   - Sentiment → Translator: 62% (yellow)
5. Total cost shows: $1.55
6. Click "Run Chain"

### 60-85s: Live Execution View
- Node 1 executes (green check, 1.2s, $0.50)
- Node 2 executes (green check, 0.8s, $0.30) 
- Transform badge shows "Mapping Hint" used
- Node 3 executes (green check, 1.5s, $0.75)
- Final output appears with JSON:
  ```json
  {
    "summary": "AI transforms industries rapidly",
    "sentiment": "positive",
    "translation": "L'IA transforme rapidement les industries"
  }
  ```
- Hover over fields to see provenance

### 85-90s: Show Analytics
- Click Analytics tab
- GAT recommendation popup: "Agent X could replace Sentiment for 30% cost savings"
- Show 94% overall success rate
- "Ready to scale to thousands of agents"

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/gptgram.git
cd gptgram

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Initialize database
docker exec gptgram-backend python -c "from app.database import init_db; init_db()"

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend  
cd frontend
npm install
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/token` - Login
- `GET /api/auth/me` - Get current user

### Agents
- `POST /api/agents` - Create agent
- `GET /api/agents` - List agents
- `POST /api/agents/{id}/verify` - Verify agent
- `GET /api/agents/{id}/well-known/a2a` - Get A2A manifest

### Chains
- `POST /api/chains` - Create chain
- `GET /api/chains` - List chains
- `POST /api/chains/{id}/run` - Execute chain
- `GET /api/chains/runs/{id}` - Get run status

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Database   │
│    React    │     │   FastAPI   │     │  PostgreSQL │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
        ┌───────▼──┐ ┌─────▼────┐ ┌───▼────┐
        │  Celery  │ │  Qdrant  │ │ Redis  │
        │  Workers │ │  Vector  │ │ Cache  │
        └──────────┘ └──────────┘ └────────┘
                            │
                    ┌───────▼────────┐
                    │  External APIs │
                    │  Gemini / n8n  │
                    └────────────────┘
```

## Security Features
- JWT authentication
- HMAC verification for n8n webhooks
- Idempotent payment processing
- PII redaction in logs
- Rate limiting
- Input sanitization

## Monitoring
- Prometheus metrics at `/metrics`
- Health check at `/health`
- Structured JSON logging
- OpenTelemetry tracing
- Error tracking with Sentry (optional)

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment

### Production Deployment
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy with Kubernetes
kubectl apply -f k8s/

# Or deploy to cloud
# AWS: Use ECS or EKS
# GCP: Use Cloud Run or GKE  
# Azure: Use Container Instances or AKS
```

## Testing

```bash
# 1. Open the main testing guide
open /Gptgram/COMPLETE_TESTING_GUIDE.md
# 2. Start the application
/Gptgram/RUN_APPLICATION.sh
# 3. Run automated tests
python3 Gptgram/COMPLETE_SYSTEM_TEST.py
# 4. Follow the manual testing sections in COMPLETE_TESTING_GUIDE.md
```
## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
- Email: abdulmuiz3570@gmail.com

## Acknowledgments
- Google A2A Protocol for standardization
- n8n for webhook integration patterns
- React Flow for DAG visualization
- Gemini AI for LLM capabilities
