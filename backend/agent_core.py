"""
agent_core.py — The central agent reasoning loop (Gemini version).
"""

import uuid
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
import google.generativeai as genai

import tools
from database import Project
from planner import Planner
from risk_analyzer import RiskAnalyzer

logger = logging.getLogger(__name__)


class AgentCore:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Add it to backend/.env"
            )

        genai.configure(api_key=api_key)
        self.prompts = tools.load_prompts("prompts.json")
        self.planner = Planner(self.prompts)
        self.risk_analyzer = RiskAnalyzer(self.prompts)
        logger.info("[AGENT] Gemini AgentCore initialized")

    def reload_prompts(self):
        self.prompts = tools.load_prompts("prompts.json")
        self.planner.prompts = self.prompts
        self.risk_analyzer.prompts = self.prompts
        logger.info("[AGENT] Prompts reloaded")

    def process_goal(self, db: Session, goal: str) -> dict:
        import hashlib
        logger.info(f"[AGENT] process_goal: {goal[:80]}...")

        project_id = str(uuid.uuid4())
        goal_hash = hashlib.md5(goal.encode()).hexdigest()

        project = Project(
            id=project_id,
            name="Initializing...",
            goal=goal,
            goal_hash=goal_hash,
            summary="",
            status="active",
            health="GREEN",
        )
        db.add(project)
        db.commit()

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="planning",
            step_number=0,
            title="🚀 Agent Activated",
            content=(
                f"New project goal received:\n\n\"{goal}\"\n\n"
                f"Starting planning loop..."
            ),
        )

        # Plan
        try:
            project, tasks = self.planner.plan(db, project_id, goal)
        except Exception as e:
            logger.error(f"[AGENT] Planner error: {e}")
            tools.log_reasoning_step(
                db, project_id=project_id, step_type="planning",
                step_number=99, title="❌ Planning Error",
                content=f"Error: {str(e)}",
            )
            tasks = []

        # Analyze risks
        risks, actions = [], []
        if tasks:
            try:
                risks, actions = self.risk_analyzer.analyze(db, project_id)
            except Exception as e:
                logger.error(f"[AGENT] Risk analysis error: {e}")

        stats = tools.get_task_stats(db, project_id)

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="planning",
            step_number=999,
            title="✅ Agent Loop Complete",
            content=(
                f"Project '{project.name}' is ready.\n\n"
                f"• {len(tasks)} tasks created\n"
                f"• {len(risks)} risks identified\n"
                f"• {len(actions)} actions recommended\n"
                f"• Health: {project.health}"
            ),
            data=stats,
        )

        return {
            "project": tools.serialize_project(project),
            "tasks": [tools.serialize_task(t) for t in tasks],
            "risks": [tools.serialize_risk(r) for r in risks],
            "actions": [tools.serialize_action(a) for a in actions],
            "stats": stats,
        }

    def handle_progress_update(
        self,
        db: Session,
        project_id: str,
        task_id: str,
        new_status: str,
        new_progress: int,
        actual_hours: float = 0.0,
    ) -> dict:
        task = tools.update_task_progress(db, task_id, new_status, new_progress, actual_hours)
        if not task:
            raise ValueError("Task not found")

        impact = self.risk_analyzer.analyze_progress_update(
            db, project_id, task_id, new_status, new_progress
        )

        if impact.get("impact_level") == "HIGH":
            try:
                self.risk_analyzer.analyze(db, project_id)
            except Exception as e:
                logger.error(f"[AGENT] Re-analysis error: {e}")

        project = tools.get_project(db, project_id)
        tasks = tools.get_tasks_for_project(db, project_id)
        risks = tools.get_risks_for_project(db, project_id)
        actions = tools.get_agent_actions(db, project_id)
        stats = tools.get_task_stats(db, project_id)

        return {
            "project": tools.serialize_project(project),
            "task": tools.serialize_task(task),
            "impact": impact,
            "tasks": [tools.serialize_task(t) for t in tasks],
            "risks": [tools.serialize_risk(r) for r in risks],
            "actions": [tools.serialize_action(a) for a in actions],
            "stats": stats,
        }