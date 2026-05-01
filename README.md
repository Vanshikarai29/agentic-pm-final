# 🚀 Agentic AI Project Manager

An AI-powered autonomous project management system that converts user goals into structured task plans, analyzes risks, and tracks execution using a Gemini-powered reasoning agent.

---

## 📌 Features

- 🧠 AI-based goal decomposition into actionable tasks  
- 📊 Automatic project planning and structuring  
- ⚠️ Intelligent risk analysis for tasks and dependencies  
- 📈 Task progress tracking (0–100%)  
- 🔁 Real-time reasoning trace (AI decision visibility)  
- 🗂️ SQLite database with SQLAlchemy ORM  
- 🌐 FastAPI backend (REST APIs)  
- ⚛️ React frontend dashboard  
- 🔄 Task status lifecycle: pending → in_progress → completed  

---

## 🏗️ Tech Stack

### Backend
- FastAPI
- Python 3.10+
- SQLAlchemy
- SQLite
- Google Gemini API

### Frontend
- React.js
- Axios
- HTML/CSS

---

## 📁 Project Structure
agentic-pm-final/
│
├── backend/
│ ├── main.py
│ ├── agent_core.py
│ ├── planner.py
│ ├── risk_analyzer.py
│ ├── tools.py
│ ├── database.py
│ ├── prompts.json
│ ├── requirements.txt
│
├── frontend/
│ ├── src/
│ ├── public/
│ ├── package.json
│
├── Makefile
├── README.md


---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/agentic-pm-final.git
cd agentic-pm-final

2️⃣ Backend Setup
cd backend
pip install -r requirements.txt

Create .env file:

GEMINI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./agentic_pm.db
CORS_ORIGINS=http://localhost:3000

Run backend server:

uvicorn main:app --reload

Backend runs at:

http://localhost:8000
3️⃣ Frontend Setup
cd frontend
npm install
npm start

Frontend runs at:

http://localhost:3000
📡 API Endpoints
🔹 Health Check
GET /health
🔹 Create AI Goal
POST /goal

Request Body:

{
  "goal": "Build a real-time chat application with authentication"
}
🔹 Get Projects
GET /projects
🔹 Get Tasks by Project
GET /tasks?project_id=<project_id>
🔹 Debug Tasks
GET /debug/tasks
POST /debug/tasks
🔹 Repair Tasks
GET /repair/tasks
POST /repair/tasks
🧠 How It Works
User submits a goal
AI Agent (Gemini) breaks it into structured tasks
Tasks are stored in database
Risk Analyzer evaluates dependencies and risks
Frontend displays live project dashboard
Progress updates dynamically reflect system state

Future Improvements
WebSocket real-time updates
Authentication system (JWT)
Multi-user collaboration
PostgreSQL support
AI task optimization engine
Cloud deployment (Render / Vercel)