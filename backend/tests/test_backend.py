"""
tests/test_backend.py — Unit and integration tests.

Run with:  pytest tests/ -v
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Patch env before imports that read it
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key-not-real")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from database import Base, get_db
from main import app
import tools


# ── Test DB Setup ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Tool Layer Tests ───────────────────────────────────────────────────────────

class TestToolsLayer:
    def test_create_project(self, test_db):
        project = tools.create_project(
            test_db,
            goal="Build a todo app",
            name="Todo App",
            summary="A simple todo application",
            rationale="Start with CRUD, then add features.",
        )
        assert project.id is not None
        assert project.name == "Todo App"
        assert project.goal == "Build a todo app"
        assert project.health == "GREEN"

    def test_create_task(self, test_db):
        project = tools.create_project(
            test_db, "Build app", "App", "An app", "Plan it first."
        )
        task = tools.create_task(
            db=test_db,
            project_id=project.id,
            title="Design DB Schema",
            description="Design the database tables",
            priority="CRITICAL",
            estimated_hours=4.0,
            dependencies=[],
            risk_level="LOW",
            reasoning="Must be done before any coding starts",
        )
        assert task.id is not None
        assert task.priority == "CRITICAL"
        assert task.status == "pending"
        assert task.progress == 0

    def test_update_task_progress(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        task = tools.create_task(
            test_db, project.id, "Task 1", "Desc", "HIGH", 8.0, [], "MEDIUM", "Because."
        )
        updated = tools.update_task_progress(test_db, task.id, "in_progress", 50, 4.0)
        assert updated.status == "in_progress"
        assert updated.progress == 50
        assert updated.actual_hours == 4.0

    def test_task_stats_empty(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        stats = tools.get_task_stats(test_db, project.id)
        assert stats["total"] == 0
        assert stats["completion_rate"] == 0

    def test_task_stats_with_tasks(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        t1 = tools.create_task(test_db, project.id, "T1", "", "HIGH", 4, [], "LOW", "")
        t2 = tools.create_task(test_db, project.id, "T2", "", "MEDIUM", 4, [], "LOW", "")
        tools.update_task_progress(test_db, t1.id, "completed", 100)
        stats = tools.get_task_stats(test_db, project.id)
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert stats["completion_rate"] == 50.0

    def test_save_and_get_risks(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        risks_data = [
            {
                "type": "SCHEDULE",
                "severity": "HIGH",
                "title": "Deadline Risk",
                "description": "Behind schedule",
                "probability": 0.8,
                "impact": 0.9,
                "suggested_action": "Add resources",
                "reasoning": "3 tasks overdue",
                "affected_tasks": [],
            }
        ]
        saved = tools.save_risks(test_db, project.id, risks_data)
        assert len(saved) == 1
        assert saved[0].severity == "HIGH"

        fetched = tools.get_risks_for_project(test_db, project.id)
        assert len(fetched) == 1

    def test_log_and_get_reasoning(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        step = tools.log_reasoning_step(
            test_db, project.id, "planning", 1, "Step 1", "Thinking..."
        )
        assert step.id is not None
        steps = tools.get_reasoning_steps(test_db, project.id)
        assert len(steps) == 1
        assert steps[0].title == "Step 1"

    def test_load_prompts(self):
        prompts = tools.load_prompts("prompts.json")
        assert "system_prompt" in prompts
        assert "planner_prompt" in prompts
        assert "risk_analysis_prompt" in prompts
        assert "{goal}" in prompts["planner_prompt"]

    def test_serialize_task(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        task = tools.create_task(test_db, project.id, "T1", "D1", "HIGH", 8, ["Dep1"], "MEDIUM", "Why")
        serialized = tools.serialize_task(task)
        assert serialized["title"] == "T1"
        assert serialized["priority"] == "HIGH"
        assert isinstance(serialized["dependencies"], list)
        assert "id" in serialized

    def test_progress_clamped(self, test_db):
        project = tools.create_project(test_db, "Test", "Test", "Test", "Test")
        task = tools.create_task(test_db, project.id, "T1", "", "HIGH", 4, [], "LOW", "")
        updated = tools.update_task_progress(test_db, task.id, "in_progress", 150)
        assert updated.progress == 100
        updated2 = tools.update_task_progress(test_db, task.id, "pending", -10)
        assert updated2.progress == 0


# ── API Endpoint Tests ─────────────────────────────────────────────────────────

class TestAPIEndpoints:
    def test_health_check(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_list_projects_empty(self, client):
        r = client.get("/projects")
        assert r.status_code == 200
        assert r.json()["data"] == []

    def test_get_tasks_not_found(self, client):
        r = client.get("/tasks?project_id=nonexistent-id")
        assert r.status_code == 404

    def test_get_risks_not_found(self, client):
        r = client.get("/risks?project_id=nonexistent-id")
        assert r.status_code == 404

    def test_get_prompts(self, client):
        r = client.get("/prompts")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "system_prompt" in data

    def test_goal_requires_min_length(self, client):
        r = client.post("/goal", json={"goal": "short"})
        assert r.status_code == 422  # Pydantic validation

    def test_update_invalid_status(self, client):
        r = client.post("/update", json={
            "project_id": "test",
            "task_id": "test",
            "status": "INVALID_STATUS",
            "progress": 50,
        })
        assert r.status_code == 422

    def test_update_progress_out_of_range(self, client):
        r = client.post("/update", json={
            "project_id": "test",
            "task_id": "test",
            "status": "in_progress",
            "progress": 150,  # > 100
        })
        assert r.status_code == 422

    def test_get_reasoning_not_found(self, client):
        r = client.get("/reasoning?project_id=nonexistent")
        assert r.status_code == 404

    def test_get_stats_not_found(self, client):
        r = client.get("/stats?project_id=nonexistent")
        assert r.status_code == 404


# ── Planner Unit Tests (no LLM) ───────────────────────────────────────────────

class TestPlanner:
    def test_fallback_plan_structure(self):
        from planner import Planner
        import anthropic

        # Create with a mock client (won't be called in fallback test)
        prompts = tools.load_prompts("prompts.json")
        mock_client = None  # Not used in _fallback_plan
        p = Planner.__new__(Planner)
        p.prompts = prompts

        plan = p._fallback_plan("Build an e-commerce website")
        assert "project_name" in plan
        assert "tasks" in plan
        assert len(plan["tasks"]) > 0
        for task in plan["tasks"]:
            assert "title" in task
            assert "priority" in task
            assert task["priority"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    def test_parse_json_from_markdown(self):
        from planner import Planner
        p = Planner.__new__(Planner)
        raw = '```json\n{"project_name": "Test", "tasks": []}\n```'
        result = p._parse_json_response(raw)
        assert result is not None
        assert result["project_name"] == "Test"

    def test_parse_json_plain(self):
        from planner import Planner
        p = Planner.__new__(Planner)
        raw = '{"project_name": "Test", "tasks": [{"title": "T1"}]}'
        result = p._parse_json_response(raw)
        assert result["project_name"] == "Test"

    def test_parse_json_invalid(self):
        from planner import Planner
        p = Planner.__new__(Planner)
        result = p._parse_json_response("this is not json at all")
        assert result is None


# ── Risk Analyzer Unit Tests ───────────────────────────────────────────────────

class TestRiskAnalyzer:
    def test_fallback_analysis_green(self):
        from risk_analyzer import RiskAnalyzer
        ra = RiskAnalyzer.__new__(RiskAnalyzer)
        stats = {
            "total": 5, "completed": 4, "in_progress": 1,
            "blocked": 0, "overdue": 0, "high_priority_pending": 0,
            "completion_rate": 80.0
        }
        result = ra._fallback_analysis(stats)
        assert result["overall_health"] == "GREEN"
        assert "risks" in result

    def test_fallback_analysis_red(self):
        from risk_analyzer import RiskAnalyzer
        ra = RiskAnalyzer.__new__(RiskAnalyzer)
        stats = {
            "total": 10, "completed": 2, "in_progress": 2,
            "blocked": 4, "overdue": 3, "high_priority_pending": 5,
            "completion_rate": 20.0
        }
        result = ra._fallback_analysis(stats)
        assert result["overall_health"] == "RED"
        assert len(result["risks"]) > 0

    def test_parse_json_list(self):
        from risk_analyzer import RiskAnalyzer
        ra = RiskAnalyzer.__new__(RiskAnalyzer)
        raw = '```json\n[{"action": "Fix it", "priority": 1}]\n```'
        result = ra._parse_json_response(raw)
        assert isinstance(result, list)
        assert result[0]["action"] == "Fix it"
