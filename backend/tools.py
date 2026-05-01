"""
tools.py — The agent's tool layer.
All DB + serialization + stats utilities used by the agent.
"""

import uuid
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from database import Project, Task, Risk, ReasoningStep, AgentAction

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# PROJECT TOOLS
# ──────────────────────────────────────────────

def create_project(db: Session, goal: str, name: str, summary: str, rationale: str) -> Project:
    project = Project(
        id=str(uuid.uuid4()),
        name=name,
        goal=goal,
        goal_hash=hashlib.md5(goal.encode()).hexdigest(),
        summary=summary,
        planning_rationale=rationale,
        status="active",
        health="GREEN",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: str):
    return db.query(Project).filter(Project.id == project_id).first()


def get_all_projects(db: Session):
    return db.query(Project).order_by(Project.created_at.desc()).all()


def update_project_health(db: Session, project_id: str, health: str, reasoning: str):
    project = get_project(db, project_id)
    if project:
        project.health = health
        project.health_reasoning = reasoning
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
    return project


# ──────────────────────────────────────────────
# TASK TOOLS
# ──────────────────────────────────────────────

def create_task(
    db: Session,
    project_id: str,
    title: str,
    description: str,
    priority: str,
    estimated_hours: float,
    dependencies: list,
    risk_level: str,
    reasoning: str,
):
    base_days = {"CRITICAL": 3, "HIGH": 7, "MEDIUM": 14, "LOW": 21}
    due_date = datetime.utcnow() + timedelta(days=base_days.get(priority, 14))

    task = Task(
        id=str(uuid.uuid4()),
        project_id=project_id,
        title=title,
        description=description,
        priority=priority,
        status="pending",
        progress=0,
        estimated_hours=estimated_hours,
        actual_hours=0,
        risk_level=risk_level,
        dependencies=dependencies,
        reasoning=reasoning,
        due_date=due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks_for_project(db: Session, project_id: str):
    return (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.created_at)
        .all()
    )


def update_task_progress(
    db: Session,
    task_id: str,
    status: str,
    progress: int,
    actual_hours: Optional[float] = None,
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    task.progress = max(0, min(100, progress))

    # Auto-sync status based on progress
    if task.progress >= 100:
        task.status = "completed"
    elif task.progress > 0:
        task.status = "in_progress"
    else:
        task.status = "pending"

    if actual_hours is not None:
        task.actual_hours = actual_hours

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def get_task_stats(db: Session, project_id: str) -> dict:
    """Aggregate stats — includes ALL keys used by risk analyzer prompts."""
    tasks = get_tasks_for_project(db, project_id)
    now = datetime.utcnow()

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completed")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    blocked = sum(1 for t in tasks if t.status == "blocked")
    pending = sum(1 for t in tasks if t.status == "pending")
    overdue = sum(
        1 for t in tasks
        if t.due_date and t.due_date < now and t.status != "completed"
    )
    high_priority_pending = sum(
        1 for t in tasks
        if t.priority in ("CRITICAL", "HIGH") and t.status in ("pending", "blocked")
    )
    total_estimated_hours = sum(t.estimated_hours or 0 for t in tasks)
    total_actual_hours = sum(t.actual_hours or 0 for t in tasks)
    completion_rate = round((completed / total) * 100, 1) if total else 0
    avg_progress = round(sum(t.progress or 0 for t in tasks) / total, 1) if total else 0

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "blocked": blocked,
        "pending": pending,
        "overdue": overdue,
        "high_priority_pending": high_priority_pending,
        "total_estimated_hours": total_estimated_hours,
        "total_actual_hours": total_actual_hours,
        "completion_rate": completion_rate,
        "avg_progress": avg_progress,
    }


def build_task_detail_string(db: Session, project_id: str) -> str:
    """Human-readable task summary injected into risk prompts."""
    tasks = get_tasks_for_project(db, project_id)
    now = datetime.utcnow()
    lines = []
    for t in tasks:
        overdue = ""
        if t.due_date and t.due_date < now and t.status != "completed":
            overdue = " OVERDUE"
        lines.append(
            f"- [{t.priority}] {t.title} | status={t.status} | "
            f"progress={t.progress}% | est={t.estimated_hours}h | "
            f"actual={t.actual_hours}h{overdue}"
        )
    return "\n".join(lines) if lines else "No tasks yet."


# ──────────────────────────────────────────────
# RISK TOOLS
# ──────────────────────────────────────────────

def save_risks(db: Session, project_id: str, risks_data: list) -> list:
    """Persist risks — returns list of Risk ORM objects (NOT dicts)."""
    db.query(Risk).filter(
        Risk.project_id == project_id,
        Risk.resolved == False
    ).delete()
    db.commit()

    saved = []
    for r in risks_data:
        risk = Risk(
            id=str(uuid.uuid4()),
            project_id=project_id,
            type=r.get("type", "GENERAL"),
            severity=r.get("severity", "MEDIUM"),
            title=r.get("title", "Unnamed Risk"),
            description=r.get("description", ""),
            affected_tasks=r.get("affected_tasks", []),
            probability=float(r.get("probability", 0.5)),
            impact=float(r.get("impact", 0.5)),
            suggested_action=r.get("suggested_action", ""),
            reasoning=r.get("reasoning", ""),
        )
        db.add(risk)
        saved.append(risk)  # ORM object, not dict

    db.commit()
    for risk in saved:
        db.refresh(risk)
    return saved


def get_risks_for_project(db: Session, project_id: str):
    return (
        db.query(Risk)
        .filter(Risk.project_id == project_id, Risk.resolved == False)
        .order_by(Risk.severity)
        .all()
    )


# ──────────────────────────────────────────────
# REASONING
# ──────────────────────────────────────────────

def log_reasoning_step(
    db, project_id, step_type, step_number, title, content, data=None
):
    step = ReasoningStep(
        id=str(uuid.uuid4()),
        project_id=project_id,
        step_type=step_type,
        step_number=step_number,
        title=title,
        content=content,
        data=data,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def get_reasoning_steps(db: Session, project_id: str):
    return (
        db.query(ReasoningStep)
        .filter(ReasoningStep.project_id == project_id)
        .order_by(ReasoningStep.created_at)
        .all()
    )


# ──────────────────────────────────────────────
# AGENT ACTIONS
# ──────────────────────────────────────────────

def save_agent_actions(db, project_id, actions_data) -> list:
    """Returns list of AgentAction ORM objects."""
    db.query(AgentAction).filter(
        AgentAction.project_id == project_id,
        AgentAction.done == False
    ).delete()
    db.commit()

    saved = []
    for a in actions_data:
        action = AgentAction(
            id=str(uuid.uuid4()),
            project_id=project_id,
            action=a.get("action", ""),
            priority=int(a.get("priority", 3)),
            impact=a.get("impact", ""),
            effort=a.get("effort", "MEDIUM"),
            task_ids_affected=a.get("task_ids_affected", []),
            reasoning=a.get("reasoning", ""),
        )
        db.add(action)
        saved.append(action)

    db.commit()
    for action in saved:
        db.refresh(action)
    return saved


def get_agent_actions(db, project_id):
    return (
        db.query(AgentAction)
        .filter(AgentAction.project_id == project_id, AgentAction.done == False)
        .order_by(AgentAction.priority)
        .all()
    )


# ──────────────────────────────────────────────
# SERIALIZERS
# ──────────────────────────────────────────────

def serialize_project(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "goal": p.goal,
        "summary": p.summary,
        "status": p.status,
        "health": p.health,
        "health_reasoning": p.health_reasoning,
        "planning_rationale": p.planning_rationale,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


def serialize_task(t: Task) -> dict:
    return {
        "id": t.id,
        "project_id": t.project_id,
        "title": t.title,
        "description": t.description,
        "priority": t.priority,
        "status": t.status,
        "progress": t.progress,
        "estimated_hours": t.estimated_hours,
        "actual_hours": t.actual_hours,
        "risk_level": t.risk_level,
        "dependencies": t.dependencies or [],
        "reasoning": t.reasoning,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


def serialize_risk(r: Risk) -> dict:
    return {
        "id": r.id,
        "project_id": r.project_id,
        "type": r.type,
        "severity": r.severity,
        "title": r.title,
        "description": r.description,
        "affected_tasks": r.affected_tasks or [],
        "probability": r.probability,
        "impact": r.impact,
        "suggested_action": r.suggested_action,
        "reasoning": r.reasoning,
        "resolved": r.resolved,
        "created_at": r.created_at.isoformat(),
    }


def serialize_reasoning_step(s: ReasoningStep) -> dict:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "step_type": s.step_type,
        "step_number": s.step_number,
        "title": s.title,
        "content": s.content,
        "data": s.data,
        "created_at": s.created_at.isoformat(),
    }


def serialize_action(a: AgentAction) -> dict:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "action": a.action,
        "priority": a.priority,
        "impact": a.impact,
        "effort": a.effort,
        "task_ids_affected": a.task_ids_affected or [],
        "reasoning": a.reasoning,
        "done": a.done,
        "created_at": a.created_at.isoformat(),
    }


# ──────────────────────────────────────────────
# PROMPTS
# ──────────────────────────────────────────────

def load_prompts(path: str = "prompts.json") -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"prompts.json not found at {path}")
        return {}