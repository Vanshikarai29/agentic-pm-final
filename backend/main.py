"""
main.py — FastAPI application entry point.
"""

import os
import json
import logging
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database import create_tables, get_db, Task, Project
import tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Agentic AI Project Manager",
    version="1.0.0",
)

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        from agent_core import AgentCore
        _agent = AgentCore()
    return _agent


# ── Request Models ─────────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    goal: str = Field(..., min_length=10, max_length=2000)


class UpdateRequest(BaseModel):
    project_id: str
    task_id: str
    status: str
    progress: int = Field(..., ge=0, le=100)
    actual_hours: Optional[float] = 0.0


class PromptsUpdateRequest(BaseModel):
    prompts: dict


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "agentic-pm-api"}


@app.post("/goal")
def submit_goal(request: GoalRequest, db: Session = Depends(get_db)):
    """Submit a project goal — agent runs full planning + risk cycle."""
    try:
        agent = get_agent()
        result = agent.process_goal(db, request.goal)
        return {"success": True, "data": result}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[API] /goal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """List all projects with stats."""
    projects = tools.get_all_projects(db)
    result = []
    for p in projects:
        stats = tools.get_task_stats(db, p.id)
        result.append({**tools.serialize_project(p), "stats": stats})
    return {"success": True, "data": result}


@app.get("/tasks")
def get_tasks(project_id: str, db: Session = Depends(get_db)):
    """Fetch all tasks for a project."""
    project = tools.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = tools.get_tasks_for_project(db, project_id)
    return {
        "success": True,
        "data": {
            "project": tools.serialize_project(project),
            "tasks": [tools.serialize_task(t) for t in tasks],
            "stats": tools.get_task_stats(db, project_id),
        },
    }


@app.post("/update")
def update_task(request: UpdateRequest, db: Session = Depends(get_db)):
    """Update task progress."""
    task = db.query(Task).filter(Task.id == request.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.progress = max(0, min(100, request.progress))
    if task.progress >= 100:
        task.status = "completed"
    elif task.progress > 0:
        task.status = "in_progress"
    else:
        task.status = "pending"

    task.actual_hours = request.actual_hours or 0.0
    db.commit()
    db.refresh(task)

    project = tools.get_project(db, request.project_id)
    tasks = tools.get_tasks_for_project(db, request.project_id)
    risks = tools.get_risks_for_project(db, request.project_id)
    actions = tools.get_agent_actions(db, request.project_id)
    stats = tools.get_task_stats(db, request.project_id)

    return {
        "success": True,
        "data": {
            "project": tools.serialize_project(project),
            "task": tools.serialize_task(task),
            "tasks": [tools.serialize_task(t) for t in tasks],
            "risks": [tools.serialize_risk(r) for r in risks],
            "actions": [tools.serialize_action(a) for a in actions],
            "stats": stats,
        },
    }


@app.get("/risks")
def get_risks(project_id: str, db: Session = Depends(get_db)):
    """Fetch current risks and recommended actions."""
    project = tools.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    risks = tools.get_risks_for_project(db, project_id)
    actions = tools.get_agent_actions(db, project_id)
    return {
        "success": True,
        "data": {
            "project_health": project.health,
            "health_reasoning": project.health_reasoning,
            "risks": [tools.serialize_risk(r) for r in risks],
            "actions": [tools.serialize_action(a) for a in actions],
        },
    }


@app.get("/reasoning")
def get_reasoning(project_id: str, db: Session = Depends(get_db)):
    """Fetch the agent's full reasoning trace."""
    project = tools.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    steps = tools.get_reasoning_steps(db, project_id)
    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "project_name": project.name,
            "steps": [tools.serialize_reasoning_step(s) for s in steps],
        },
    }


@app.get("/actions")
def get_actions(project_id: str, db: Session = Depends(get_db)):
    """Fetch recommended agent actions."""
    actions = tools.get_agent_actions(db, project_id)
    return {"success": True, "data": [tools.serialize_action(a) for a in actions]}


@app.get("/stats")
def get_stats(project_id: str, db: Session = Depends(get_db)):
    """Get aggregate statistics for a project."""
    project = tools.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "data": tools.get_task_stats(db, project_id)}


@app.get("/prompts")
def get_prompts():
    """Read current prompts from prompts.json."""
    prompts = tools.load_prompts("prompts.json")
    return {"success": True, "data": prompts}


@app.post("/prompts")
def update_prompts(request: PromptsUpdateRequest):
    """Update prompts.json and hot-reload the agent."""
    try:
        with open("prompts.json", "w") as f:
            json.dump(request.prompts, f, indent=2)
        if _agent:
            _agent.reload_prompts()
        return {"success": True, "message": "Prompts updated and reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risks/reanalyze")
def reanalyze_risks(project_id: str, db: Session = Depends(get_db)):
    """Trigger a fresh risk analysis cycle."""
    project = tools.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        agent = get_agent()
        risks, actions = agent.risk_analyzer.analyze(db, project_id)
        return {
            "success": True,
            "data": {
                "risks": [tools.serialize_risk(r) for r in risks],
                "actions": [tools.serialize_action(a) for a in actions],
            },
        }
    except Exception as e:
        logger.error(f"[API] /risks/reanalyze error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/tasks")
def debug_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return {
        "total": len(tasks),
        "data": [{"id": t.id, "title": t.title, "status": t.status, "progress": t.progress} for t in tasks],
    }


@app.get("/repair/tasks")
def repair_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    for t in tasks:
        if t.progress >= 100:
            t.status = "completed"
        elif t.progress > 0:
            t.status = "in_progress"
        else:
            t.status = "pending"
    db.commit()
    return {"success": True, "message": f"Repaired {len(tasks)} tasks"}