"""
risk_analyzer.py — Risk detection and action-suggestion module (Gemini version).
"""

import json
import logging
import re
from typing import Optional
import google.generativeai as genai
import os
from sqlalchemy.orm import Session

import tools
from database import Project, Risk, AgentAction

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


class RiskAnalyzer:

    def __init__(self, prompts: dict):
        self.prompts = prompts
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # gemini-pro is deprecated — use gemini-1.5-flash
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _call_gemini(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"[RISK] Gemini API error: {e}")
            return ""

    def analyze(self, db: Session, project_id: str) -> tuple[list, list]:
        project = tools.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        stats = tools.get_task_stats(db, project_id)
        task_details = tools.build_task_detail_string(db, project_id)

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="risk_analysis",
            step_number=100,
            title="📊 Collecting Project State",
            content=(
                f"Gathering state for risk analysis:\n"
                f"• Total: {stats['total']} | Completed: {stats['completed']}\n"
                f"• In Progress: {stats['in_progress']} | Blocked: {stats['blocked']}\n"
                f"• Overdue: {stats['overdue']} | High Priority Pending: {stats['high_priority_pending']}"
            ),
            data=stats,
        )

        prompt_template = self.prompts.get("risk_analysis_prompt", "")
        system_prompt = self.prompts.get("system_prompt", "")

        user_prompt = (
            prompt_template
            .replace("{project_name}", project.name)
            .replace("{total_tasks}", str(stats["total"]))
            .replace("{completed_tasks}", str(stats["completed"]))
            .replace("{in_progress_tasks}", str(stats["in_progress"]))
            .replace("{blocked_tasks}", str(stats["blocked"]))
            .replace("{overdue_tasks}", str(stats["overdue"]))
            .replace("{high_priority_pending}", str(stats["high_priority_pending"]))
            .replace("{task_details}", task_details)
        )

        full_prompt = system_prompt + "\n\n" + user_prompt
        raw = self._call_gemini(full_prompt)
        analysis = self._parse_json_response(raw)

        if not analysis:
            logger.warning("[RISK] Falling back to default analysis")
            analysis = self._fallback_analysis(stats)

        overall_health = analysis.get("overall_health", "YELLOW")
        health_reasoning = analysis.get("health_reasoning", "")
        risks_data = analysis.get("risks", [])

        tools.update_project_health(db, project_id, overall_health, health_reasoning)

        health_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(overall_health, "⚪")
        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="risk_analysis",
            step_number=101,
            title=f"{health_emoji} Project Health: {overall_health}",
            content=f"{health_reasoning}\n\nTop Recommendation: {analysis.get('top_recommendation', '')}",
            data={"health": overall_health, "risk_count": len(risks_data)},
        )

        # save_risks now returns ORM objects
        saved_risks = tools.save_risks(db, project_id, risks_data)

        for i, risk in enumerate(saved_risks):
            tools.log_reasoning_step(
                db,
                project_id=project_id,
                step_type="risk_analysis",
                step_number=102 + i,
                title=f"⚠️ Risk [{risk.severity}]: {risk.title}",
                content=(
                    f"Type: {risk.type}\n"
                    f"Probability: {risk.probability:.0%} | Impact: {risk.impact:.0%}\n\n"
                    f"Description: {risk.description}\n\n"
                    f"Suggested Action: {risk.suggested_action}"
                ),
                data=tools.serialize_risk(risk),
            )

        actions = self._generate_actions(db, project_id, analysis, stats)
        return saved_risks, actions

    def _generate_actions(self, db, project_id, analysis, stats) -> list:
        risks_summary = "\n".join(
            f"- [{r.get('severity','?')}] {r.get('title','')}: {r.get('suggested_action','')}"
            for r in analysis.get("risks", [])
        )

        project_state = (
            f"Completion: {stats['completion_rate']}% | "
            f"Blocked: {stats['blocked']} | "
            f"Overdue: {stats['overdue']} | "
            f"Health: {analysis.get('overall_health', 'YELLOW')}"
        )

        prompt_template = self.prompts.get("action_suggestion_prompt", "")
        system_prompt = self.prompts.get("system_prompt", "")

        user_prompt = (
            prompt_template
            .replace("{project_state}", project_state)
            .replace("{risks}", risks_summary)
        )

        full_prompt = system_prompt + "\n\n" + user_prompt
        raw = self._call_gemini(full_prompt)
        actions_data = self._parse_json_response(raw)

        if isinstance(actions_data, dict):
            actions_data = actions_data.get("actions", [])
        if not isinstance(actions_data, list):
            actions_data = []

        saved_actions = tools.save_agent_actions(db, project_id, actions_data)

        if saved_actions:
            tools.log_reasoning_step(
                db,
                project_id=project_id,
                step_type="action",
                step_number=200,
                title=f"🎯 {len(saved_actions)} Recommended Actions",
                content="\n".join(
                    f"{i+1}. [{a.effort}] {a.action}"
                    for i, a in enumerate(saved_actions)
                ),
            )

        return saved_actions

    def analyze_progress_update(
        self, db, project_id, task_id, new_status, new_progress
    ) -> dict:
        task_list = tools.get_tasks_for_project(db, project_id)
        updated_task = next((t for t in task_list if t.id == task_id), None)
        if not updated_task:
            return {}

        stats = tools.get_task_stats(db, project_id)

        prompt_template = self.prompts.get("progress_analysis_prompt", "")
        system_prompt = self.prompts.get("system_prompt", "")

        user_prompt = (
            prompt_template
            .replace("{task_title}", updated_task.title)
            .replace("{new_status}", new_status)
            .replace("{new_progress}", str(new_progress))
            .replace("{project_context}", str(stats))
        )

        full_prompt = system_prompt + "\n\n" + user_prompt
        raw = self._call_gemini(full_prompt)
        impact = self._parse_json_response(raw) or {}

        tools.log_reasoning_step(
            db,
            project_id=project_id,
            step_type="progress_update",
            step_number=300,
            title=f"📈 Progress Update: {updated_task.title} → {new_status}",
            content=(
                f"Impact Level: {impact.get('impact_level', 'UNKNOWN')}\n"
                f"Critical Path Affected: {impact.get('critical_path_affected', False)}\n\n"
                f"Reasoning: {impact.get('reasoning', '')}"
            ),
            data=impact,
        )

        return impact

    def _parse_json_response(self, raw: str) -> Optional[dict | list]:
        if not raw:
            return None
        patterns = [
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
            r"(\[[\s\S]+\])",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    continue
        try:
            return json.loads(raw)
        except Exception:
            return None

    def _fallback_analysis(self, stats: dict) -> dict:
        health = "GREEN"
        if stats.get("overdue", 0) > 0 or stats.get("blocked", 0) > 1:
            health = "YELLOW"
        if stats.get("overdue", 0) > 2 or stats.get("blocked", 0) > 3:
            health = "RED"

        risks = []
        if stats.get("overdue", 0) > 0:
            risks.append({
                "type": "SCHEDULE",
                "severity": "HIGH",
                "title": "Overdue Tasks Detected",
                "description": f"{stats['overdue']} task(s) past due date.",
                "probability": 0.9,
                "impact": 0.7,
                "suggested_action": "Review and re-prioritize overdue tasks immediately.",
                "reasoning": "Overdue tasks compound schedule slippage.",
                "affected_tasks": [],
            })
        if stats.get("blocked", 0) > 0:
            risks.append({
                "type": "DEPENDENCY",
                "severity": "HIGH",
                "title": "Blocked Tasks",
                "description": f"{stats['blocked']} task(s) are blocked.",
                "probability": 1.0,
                "impact": 0.8,
                "suggested_action": "Identify and remove blockers immediately.",
                "reasoning": "Blocked tasks halt downstream work.",
                "affected_tasks": [],
            })

        return {
            "overall_health": health,
            "health_reasoning": f"Based on {stats['completion_rate']}% completion with {stats.get('overdue',0)} overdue tasks.",
            "risks": risks,
            "top_recommendation": "Focus on unblocking critical-path tasks first.",
        }