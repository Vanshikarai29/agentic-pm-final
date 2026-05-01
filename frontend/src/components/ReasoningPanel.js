import React, { useState, useRef, useEffect } from 'react';

const STEP_TYPE_CONFIG = {
  planning: { color: '#6366f1', icon: '⬡', label: 'Planning' },
  risk_analysis: { color: '#f97316', icon: '◈', label: 'Risk Analysis' },
  action: { color: '#22c55e', icon: '◎', label: 'Action' },
  progress_update: { color: '#3b82f6', icon: '●', label: 'Progress Update' },
};

function StepCard({ step, index, expanded, onToggle }) {
  const tc = STEP_TYPE_CONFIG[step.step_type] || STEP_TYPE_CONFIG.planning;
  const time = new Date(step.created_at).toLocaleTimeString();

  return (
    <div className={`reasoning-step ${expanded ? 'expanded' : ''}`}>
      {/* Timeline connector */}
      <div className="step-timeline">
        <div className="step-dot" style={{ background: tc.color }} />
        {index > 0 && <div className="step-line" style={{ background: tc.color + '40' }} />}
      </div>

      <div className="step-card-body">
        <div className="step-header" onClick={onToggle}>
          <div className="step-meta">
            <span className="step-type-badge" style={{ color: tc.color, borderColor: tc.color + '40' }}>
              <span>{tc.icon}</span>
              <span>{tc.label}</span>
            </span>
            <span className="step-time">{time}</span>
          </div>
          <div className="step-title-row">
            <h4 className="step-title">{step.title}</h4>
            <button className="step-toggle">{expanded ? '▲' : '▼'}</button>
          </div>
        </div>

        {expanded && (
          <div className="step-content">
            <pre className="step-text">{step.content}</pre>
            {step.data && (
              <div className="step-data">
                <div className="data-label">Structured Data:</div>
                <pre className="step-data-json">
                  {JSON.stringify(step.data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ReasoningPanel({ project, steps }) {
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [filter, setFilter] = useState('all');
  const [autoExpand, setAutoExpand] = useState(true);
  const bottomRef = useRef(null);

  // Auto-expand latest step
  useEffect(() => {
    if (autoExpand && steps.length > 0) {
      setExpandedIds(new Set([steps[steps.length - 1].id]));
    }
  }, [steps, autoExpand]);

  const toggleStep = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => setExpandedIds(new Set(steps.map((s) => s.id)));
  const collapseAll = () => setExpandedIds(new Set());

  const filtered = filter === 'all' ? steps : steps.filter((s) => s.step_type === filter);

  const typeGroups = steps.reduce((acc, s) => {
    acc[s.step_type] = (acc[s.step_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="reasoning-panel">
      <div className="reasoning-header">
        <div className="reasoning-title-row">
          <h2 className="reasoning-title">
            <span className="title-icon">◎</span>
            Agent Reasoning Trace
          </h2>
          <div className="reasoning-actions">
            <label className="auto-expand-toggle">
              <input
                type="checkbox"
                checked={autoExpand}
                onChange={(e) => setAutoExpand(e.target.checked)}
              />
              <span>Auto-expand latest</span>
            </label>
            <button className="control-btn" onClick={expandAll}>Expand All</button>
            <button className="control-btn" onClick={collapseAll}>Collapse All</button>
          </div>
        </div>

        <p className="reasoning-subtitle">
          Every decision the agent made — in order. This is its complete chain of thought.
        </p>

        {/* Filter tabs */}
        <div className="reasoning-filters">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All <span className="filter-count">{steps.length}</span>
          </button>
          {Object.entries(STEP_TYPE_CONFIG).map(([type, cfg]) => (
            typeGroups[type] ? (
              <button
                key={type}
                className={`filter-btn ${filter === type ? 'active' : ''}`}
                style={filter === type ? { borderColor: cfg.color, color: cfg.color } : {}}
                onClick={() => setFilter(type)}
              >
                {cfg.icon} {cfg.label}
                <span className="filter-count">{typeGroups[type]}</span>
              </button>
            ) : null
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">◎</span>
          <p>No reasoning steps yet. Submit a goal to watch the agent think.</p>
        </div>
      ) : (
        <div className="reasoning-timeline">
          {filtered.map((step, index) => (
            <StepCard
              key={step.id}
              step={step}
              index={index}
              expanded={expandedIds.has(step.id)}
              onToggle={() => toggleStep(step.id)}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      {steps.length > 0 && (
        <div className="reasoning-stats">
          <span className="rstat">
            <span>⬡</span> {typeGroups.planning || 0} Planning steps
          </span>
          <span className="rstat">
            <span>◈</span> {typeGroups.risk_analysis || 0} Risk analysis steps
          </span>
          <span className="rstat">
            <span>◎</span> {typeGroups.action || 0} Action steps
          </span>
          <span className="rstat">
            <span>●</span> {typeGroups.progress_update || 0} Progress updates
          </span>
        </div>
      )}
    </div>
  );
}
