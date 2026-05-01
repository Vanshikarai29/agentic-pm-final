"""
Database layer — SQLite via SQLAlchemy (sync engine for simplicity).
All models live here; tools.py handles higher-level CRUD.
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Float,
    Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentic_pm.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ──────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, default="active")          # active | completed | archived
    health = Column(String, default="GREEN")            # GREEN | YELLOW | RED
    health_reasoning = Column(Text, nullable=True)
    planning_rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    reasoning_steps = relationship("ReasoningStep", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="MEDIUM")         # CRITICAL | HIGH | MEDIUM | LOW
    status = Column(String, default="pending")          # pending | in_progress | blocked | completed
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)
    progress = Column(Integer, default=0)               # 0-100
    risk_level = Column(String, default="MEDIUM")       # HIGH | MEDIUM | LOW
    dependencies = Column(JSON, default=list)           # list of task titles
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="tasks")


class Risk(Base):
    __tablename__ = "risks"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    type = Column(String, nullable=False)               # SCHEDULE | RESOURCE | DEPENDENCY | SCOPE | QUALITY
    severity = Column(String, default="MEDIUM")         # CRITICAL | HIGH | MEDIUM | LOW
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    affected_tasks = Column(JSON, default=list)
    probability = Column(Float, default=0.5)
    impact = Column(Float, default=0.5)
    suggested_action = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="risks")


class ReasoningStep(Base):
    __tablename__ = "reasoning_steps"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    step_type = Column(String, nullable=False)          # planning | risk_analysis | action | progress_update
    step_number = Column(Integer, default=0)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)                  # optional structured data snapshot
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="reasoning_steps")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    action = Column(Text, nullable=False)
    priority = Column(Integer, default=3)
    impact = Column(Text, nullable=True)
    effort = Column(String, default="MEDIUM")
    task_ids_affected = Column(JSON, default=list)
    reasoning = Column(Text, nullable=True)
    done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()