"""
planner.py — Task decomposition module (google.genai version with JSON mode).
"""

import json
import logging
import re
from typing import Optional
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

import tools
from database import Project, Task

logger = logging.getLogger(__name__)


class Planner:

    def __init__(self, prompts: dict, client: genai.Client):
        self.prompts = prompts
        self.client = client

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini with JSON response mode forced."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"[PLANNER] Gemini error: {e}")
            return ""

    def plan(self, db: Session, project_id: str, goal: str) -> tuple[Project, list[Task]]:
        logger.info(f"[PLANNER] Planning: {goal[:80]}...")

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="planning",
            step_number=1,
            title="🔍 Understanding Project Goal",
            content=f"Analyzing goal: '{goal}'",
        )

        prompt_template = self.prompts.get("planner_prompt", "")
        user_prompt = prompt_template.replace("{goal}", goal)

        # Reinforce JSON-only output in the prompt itself
        user_prompt += "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no code fences. Just the raw JSON object."

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="planning",
            step_number=2,
            title="🧠 Generating Task Breakdown",
            content="Calling Gemini to decompose goal into prioritized tasks...",
        )

        raw = self._call_gemini(user_prompt)
        logger.info(f"[PLANNER] Raw Gemini response (first 300 chars): {raw[:300]}")

        plan_data = self._parse_json_response(raw)

        if not plan_data:
            logger.warning("[PLANNER] JSON parse failed — using fallback plan")
            plan_data = self._fallback_plan(goal)

        project_name = plan_data.get("project_name", "Untitled Project")
        project_summary = plan_data.get("project_summary", goal)
        planning_rationale = plan_data.get("planning_rationale", "")
        tasks_data = plan_data.get("tasks", [])

        # Update project record
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.name = project_name
            project.summary = project_summary
            project.planning_rationale = planning_rationale
            db.commit()
            db.refresh(project)

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="planning",
            step_number=3,
            title=f"📋 Plan Ready: {len(tasks_data)} Tasks",
            content=(
                f"Project: {project_name}\n\n"
                f"Summary: {project_summary}\n\n"
                f"Rationale: {planning_rationale}"
            ),
            data={"task_count": len(tasks_data), "project_name": project_name},
        )

        # Save tasks
        saved_tasks = []
        for i, td in enumerate(tasks_data):
            task = tools.create_task(
                db=db,
                project_id=project_id,
                title=td.get("title", f"Task {i+1}"),
                description=td.get("description", ""),
                priority=td.get("priority", "MEDIUM"),
                estimated_hours=float(td.get("estimated_hours", 4)),
                dependencies=td.get("dependencies", []),
                risk_level=td.get("risk_level", "MEDIUM"),
                reasoning=td.get("reasoning", ""),
            )
            saved_tasks.append(task)

            tools.log_reasoning_step(
                db,
                project_id=project_id,
                step_type="planning",
                step_number=4 + i,
                title=f"✅ Task {i+1}: {task.title}",
                content=(
                    f"Priority: {task.priority} | Risk: {task.risk_level} | "
                    f"Estimate: {task.estimated_hours}h\n\n"
                    f"Reasoning: {task.reasoning}\n\n"
                    f"Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}"
                ),
                data=tools.serialize_task(task),
            )

        return project, saved_tasks

    def _parse_json_response(self, raw: str) -> Optional[dict]:
        if not raw:
            return None
        raw = raw.strip()
        # Remove markdown fences if present
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"(\{[\s\S]*\})",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception as e:
                    logger.warning(f"[PLANNER] Pattern parse failed: {e}")
        try:
            return json.loads(raw)
        except Exception as e:
            logger.error(f"[PLANNER] Final JSON parse failed: {e}\nRaw: {raw[:500]}")
            return None

    def _fallback_plan(self, goal: str) -> dict:
        return {
            "project_name": goal[:80],
            "project_summary": goal,
            "planning_rationale": "Fallback plan — AI response could not be parsed.",
            "tasks": [
                {
                    "title": "Requirements Analysis",
                    "description": "Gather and document all project requirements",
                    "priority": "CRITICAL",
                    "estimated_hours": 8,
                    "dependencies": [],
                    "risk_level": "MEDIUM",
                    "reasoning": "Must understand scope before building",
                },
                {
                    "title": "Architecture Design",
                    "description": "Design the overall system architecture",
                    "priority": "HIGH",
                    "estimated_hours": 16,
                    "dependencies": ["Requirements Analysis"],
                    "risk_level": "HIGH",
                    "reasoning": "Architecture decisions affect all downstream work",
                },
                {
                    "title": "Core Implementation",
                    "description": "Build the main features",
                    "priority": "HIGH",
                    "estimated_hours": 40,
                    "dependencies": ["Architecture Design"],
                    "risk_level": "MEDIUM",
                    "reasoning": "Primary deliverable",
                },
                {
                    "title": "Testing & QA",
                    "description": "Write and run tests, fix bugs",
                    "priority": "HIGH",
                    "estimated_hours": 16,
                    "dependencies": ["Core Implementation"],
                    "risk_level": "MEDIUM",
                    "reasoning": "Quality gate before delivery",
                },
                {
                    "title": "Deployment",
                    "description": "Deploy to production",
                    "priority": "MEDIUM",
                    "estimated_hours": 8,
                    "dependencies": ["Testing & QA"],
                    "risk_level": "HIGH",
                    "reasoning": "Final delivery milestone",
                },
            ],
        }
