import React, { useState, useEffect } from "react";
import { useProject } from "./hooks/useProject";
import GoalInput from "./components/GoalInput";
import TaskDashboard from "./components/TaskDashboard";
import RiskPanel from "./components/RiskPanel";
import ReasoningPanel from "./components/ReasoningPanel";
import PromptsEditor from "./components/PromptsEditor";
import AgentStatusBar from "./components/AgentStatusBar";
import { listProjects } from "./api/client";
import "./App.css";

const NAV_TABS = [
  { id: "tasks", label: "Task Dashboard", icon: "⬡" },
  { id: "risks", label: "Risk Panel", icon: "◈" },
  { id: "reasoning", label: "Agent Reasoning", icon: "◎" },
  { id: "prompts", label: "Prompt Config", icon: "◧" },
];

export default function App() {
  const {
    project,
    tasks,
    risks,
    actions,
    reasoning,
    stats,
    loading,
    agentThinking,
    error,
    activeStep,
    clearError,
    submitGoal,
    loadProject,
    updateTask,
    reanalyze,
  } = useProject();

  const [activeTab, setActiveTab] = useState("tasks");
  const [projects, setProjects] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [hasProject, setHasProject] = useState(false);

  useEffect(() => {
    listProjects().then(setProjects).catch(console.error);
  }, [project]);

  const handleGoalSubmit = async (goal) => {
    const p = await submitGoal(goal);
    if (p) {
      setHasProject(true);
      setActiveTab("tasks");
    }
  };

  const handleSelectProject = async (p) => {
    await loadProject(p.id);
    setHasProject(true);
    setActiveTab("tasks");
    setSidebarOpen(false);
  };

  return (
    <div className="app-root">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <span className="toggle-icon">⊞</span>
          </button>

          <div className="brand">
            <span className="brand-icon">◈</span>
            <span className="brand-name">AgentPM</span>
            <span className="brand-tag">autonomous project intelligence</span>
          </div>
        </div>

        {project && (
          <div className="header-project">
            <span
              className={`health-badge health-${project.health?.toLowerCase()}`}
            >
              {project.health === "GREEN"
                ? "●"
                : project.health === "YELLOW"
                  ? "◉"
                  : "○"}
              {project.health}
            </span>
            <span className="project-name-header">{project.name}</span>
          </div>
        )}

        <div className="header-right">
          {agentThinking && (
            <div className="agent-thinking-badge">
              <span className="thinking-dot" />
              <span className="thinking-dot delay-1" />
              <span className="thinking-dot delay-2" />
              <span className="thinking-label">Agent reasoning</span>
            </div>
          )}
        </div>
      </header>

      {/* Agent Status Bar */}
      {(agentThinking || activeStep) && (
        <AgentStatusBar message={activeStep} thinking={agentThinking} />
      )}

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠</span>
          <span>{error}</span>
          <button onClick={clearError} className="error-close">
            ✕
          </button>
        </div>
      )}

      {/* Content */}
      {!hasProject ? (
        <div className="goal-scroll-wrap">
          <GoalInput onSubmit={handleGoalSubmit} loading={loading} />
        </div>
      ) : (
        <div className="workspace">
          {/* Nav tabs */}
          <nav className="workspace-nav">
            {NAV_TABS.map((tab) => (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>

                {tab.id === "risks" && risks.length > 0 && (
                  <span className="tab-badge">{risks.length}</span>
                )}

                {tab.id === "reasoning" && reasoning.length > 0 && (
                  <span className="tab-badge tab-badge-blue">
                    {reasoning.length}
                  </span>
                )}
              </button>
            ))}
          </nav>

          {/* Tab content */}
          <div className="workspace-content">
            {activeTab === "tasks" && (
              <TaskDashboard
                project={project}
                tasks={tasks}
                stats={stats}
                onUpdateTask={updateTask}
                agentThinking={agentThinking}
              />
            )}

            {activeTab === "risks" && (
              <RiskPanel
                project={project}
                risks={risks}
                actions={actions}
                onReanalyze={reanalyze}
                agentThinking={agentThinking}
              />
            )}

            {activeTab === "reasoning" && (
              <ReasoningPanel project={project} steps={reasoning} />
            )}

            {activeTab === "prompts" && <PromptsEditor />}
          </div>
        </div>
      )}
    </div>
  );
}
