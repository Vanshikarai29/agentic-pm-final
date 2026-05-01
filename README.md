# AgentPM — Agentic AI Project Manager

> Autonomous sprint planning, risk prediction, and task optimization powered by Claude.

![AgentPM Architecture](https://via.placeholder.com/900x400/0a0b0f/6366f1?text=AgentPM+Architecture)

## What makes this an *agent* (not a chatbot)?

| Chatbot | AgentPM Agent |
|---------|---------------|
| Responds to messages | Acts autonomously on goals |
| No memory between turns | Persists all state in SQLite |
| No tool usage | Uses DB, planner, risk analyzer |
| No planning | Multi-step reasoning loop |
| No reasoning trace | Full chain-of-thought logged |

The agent runs a deterministic **6-step reasoning loop**:

```
Goal → Understand → Plan → Store Tasks → Analyze Risks → Suggest Actions → Track Progress
```

Every decision is logged as a reasoning step visible in the UI.

---

## Architecture

```
agentic-pm/
├── backend/
│   ├── agent_core.py       # 🧠 Main reasoning orchestrator
│   ├── planner.py          # 📋 Task decomposition module
│   ├── risk_analyzer.py    # ⚠️  Risk detection + action suggestion
│   ├── tools.py            # 🔧 DB + helper tool functions
│   ├── database.py         # 🗄️  SQLAlchemy models (SQLite)
│   ├── main.py             # 🌐 FastAPI endpoints
│   ├── prompts.json        # 📝 All LLM prompts (editable!)
│   ├── .env.example        # 🔑 Environment variables template
│   ├── requirements.txt
│   └── tests/
│       └── test_backend.py # ✅ Unit + API tests
│
└── frontend/
    ├── src/
    │   ├── App.js           # Root layout + routing
    │   ├── App.css          # Full design system
    │   ├── api/client.js    # API calls
    │   ├── hooks/useProject.js  # State management
    │   └── components/
    │       ├── GoalInput.js       # Project goal entry
    │       ├── TaskDashboard.js   # Tasks + progress + stats
    │       ├── RiskPanel.js       # Risks + agent actions
    │       ├── ReasoningPanel.js  # 🔥 Full agent trace
    │       ├── PromptsEditor.js   # Live prompt editing
    │       └── AgentStatusBar.js  # Sidebar + status
    └── package.json
```

---

## Agent Reasoning Trace Example

```
🚀 Agent Activated
   "Build a real-time collaborative editor with offline support"
   Starting reasoning loop...

🔍 Understanding Project Goal
   Analyzing scope, deliverables, success criteria...

🧠 Generating Task Breakdown
   Strategy: identify critical path first, then parallel workstreams...

📋 Plan Generated: 8 Tasks
   Project: Real-Time Collaborative Editor
   Planning Rationale: WebSocket server is the critical path...

✅ Task 1: WebSocket Server Setup
   Priority: CRITICAL | Risk: HIGH | Estimate: 16h
   Reasoning: All real-time features depend on this foundation

⚠️ Risk [HIGH]: Offline Sync Conflict
   Type: DEPENDENCY | Probability: 75% | Impact: 85%
   Reasoning: CRDT implementation is complex and time-intensive

🎯 3 Recommended Actions
   1. [LOW effort] Spike CRDT library (Yjs) before architecture commit
   2. [MEDIUM] Add WebSocket connection pooling early
   3. [HIGH] Plan 20% buffer for conflict resolution edge cases
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key ([get one here](https://console.anthropic.com))

### 1. Clone & setup backend

```bash
cd agentic-pm/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
nano .env

# Start the API server
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### 2. Setup frontend

```bash
cd agentic-pm/frontend

# Install dependencies
npm install

# Start React dev server
npm start
```

Frontend runs at: **http://localhost:3000**

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/goal` | Submit project goal — triggers full agent loop |
| `GET` | `/projects` | List all projects |
| `GET` | `/tasks?project_id=` | Get tasks for a project |
| `POST` | `/update` | Update task progress — triggers re-analysis |
| `GET` | `/risks?project_id=` | Get risks + agent actions |
| `GET` | `/reasoning?project_id=` | Get full agent reasoning trace |
| `GET` | `/actions?project_id=` | Get recommended actions |
| `GET` | `/stats?project_id=` | Get project statistics |
| `GET` | `/prompts` | Read current prompts |
| `POST` | `/prompts` | Update prompts (hot-reload) |
| `POST` | `/risks/reanalyze?project_id=` | Trigger fresh risk analysis |

### Example API calls

```bash
# Submit a goal
curl -X POST http://localhost:8000/goal \
  -H "Content-Type: application/json" \
  -d '{"goal": "Build an e-commerce platform with payment processing"}'

# Get tasks
curl http://localhost:8000/tasks?project_id=<project_id>

# Update task progress
curl -X POST http://localhost:8000/update \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<id>",
    "task_id": "<task_id>",
    "status": "in_progress",
    "progress": 60,
    "actual_hours": 6.5
  }'

# Get agent reasoning trace
curl http://localhost:8000/reasoning?project_id=<project_id>
```

---

## Editing Prompts

All LLM prompts are stored in `backend/prompts.json`. You can edit them:

1. **Via the UI**: Go to the "Prompt Config" tab — changes apply instantly.
2. **Via file**: Edit `prompts.json` directly, then `POST /prompts` or restart.
3. **Hot-reload**: `POST /prompts` updates the running agent without restart.

Available prompt keys:
- `system_prompt` — Agent identity, applied to all LLM calls
- `planner_prompt` — Task decomposition logic. Variable: `{goal}`
- `risk_analysis_prompt` — Risk detection. Variables: `{project_name}`, `{task_details}`, etc.
- `action_suggestion_prompt` — Generates recommendations. Variables: `{project_state}`, `{risks}`
- `progress_analysis_prompt` — Impact analysis on task update

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Expected output:
```
tests/test_backend.py::TestToolsLayer::test_create_project PASSED
tests/test_backend.py::TestToolsLayer::test_create_task PASSED
tests/test_backend.py::TestToolsLayer::test_update_task_progress PASSED
...
tests/test_backend.py::TestAPIEndpoints::test_health_check PASSED
tests/test_backend.py::TestAPIEndpoints::test_get_prompts PASSED
...
tests/test_backend.py::TestPlanner::test_fallback_plan_structure PASSED
tests/test_backend.py::TestRiskAnalyzer::test_fallback_analysis_green PASSED
...
26 passed in Xs
```

---

## Environment Variables

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (defaults shown)
DATABASE_URL=sqlite:///./agentic_pm.db
APP_ENV=development
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

---

## Security

- API key stored in `.env` only — never hardcoded
- `.env` is git-ignored
- CORS configured via environment variable
- Input validation via Pydantic on all endpoints
- No secrets in source code

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | Anthropic Claude (claude-sonnet-4) |
| Backend | FastAPI + Python 3.11 |
| Database | SQLite via SQLAlchemy |
| Frontend | React 18 |
| Charts | Recharts |
| Fonts | Syne + IBM Plex Mono |
| Tests | pytest + FastAPI TestClient |

---

## Zip the project

```bash
# From the parent directory of agentic-pm/
zip -r agentic-pm.zip agentic-pm/ \
  --exclude "agentic-pm/backend/venv/*" \
  --exclude "agentic-pm/backend/__pycache__/*" \
  --exclude "agentic-pm/backend/*.db" \
  --exclude "agentic-pm/backend/.env" \
  --exclude "agentic-pm/frontend/node_modules/*" \
  --exclude "agentic-pm/frontend/build/*"

echo "Created agentic-pm.zip"
```

---

## License

MIT
