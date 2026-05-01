import React from 'react';

export function ProjectSidebar({ open, projects, currentProject, onSelect, onClose, onNew }) {
  const healthColors = { GREEN: '#22c55e', YELLOW: '#eab308', RED: '#ef4444' };

  return (
    <>
      {open && <div className="sidebar-overlay" onClick={onClose} />}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-title">Projects</span>
          <button className="sidebar-close" onClick={onClose}>✕</button>
        </div>

        <button className="new-project-btn" onClick={onNew}>
          <span>+</span>
          <span>New Project</span>
        </button>

        <div className="project-list">
          {projects.length === 0 && (
            <div className="sidebar-empty">No projects yet</div>
          )}
          {projects.map((p) => (
            <button
              key={p.id}
              className={`project-item ${currentProject?.id === p.id ? 'active' : ''}`}
              onClick={() => onSelect(p)}
            >
              <div className="project-item-header">
                <span
                  className="project-health-dot"
                  style={{ background: healthColors[p.health] || healthColors.GREEN }}
                />
                <span className="project-item-name">{p.name}</span>
              </div>
              {p.stats && (
                <div className="project-item-stats">
                  <span>{p.stats.completion_rate}% done</span>
                  <span>{p.stats.total} tasks</span>
                </div>
              )}
              <div className="project-item-date">
                {new Date(p.created_at).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      </aside>
    </>
  );
}

export default function AgentStatusBar({ message, thinking }) {
  return (
    <div className="agent-status-bar">
      <div className="status-bar-inner">
        <div className="status-dots">
          <span className="sdot" />
          <span className="sdot delay-1" />
          <span className="sdot delay-2" />
        </div>
        <span className="status-message">{message || 'Agent is processing...'}</span>
      </div>
    </div>
  );
}
