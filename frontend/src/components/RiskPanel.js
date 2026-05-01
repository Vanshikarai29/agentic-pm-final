import React from 'react';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', icon: '◉', order: 0 },
  HIGH: { color: '#f97316', bg: 'rgba(249,115,22,0.08)', icon: '●', order: 1 },
  MEDIUM: { color: '#eab308', bg: 'rgba(234,179,8,0.08)', icon: '◎', order: 2 },
  LOW: { color: '#22c55e', bg: 'rgba(34,197,94,0.08)', icon: '○', order: 3 },
};

const RISK_TYPE_ICONS = {
  SCHEDULE: '◷',
  RESOURCE: '◈',
  DEPENDENCY: '⇢',
  SCOPE: '⬡',
  QUALITY: '◧',
};

const EFFORT_CONFIG = {
  LOW: { color: '#22c55e', label: 'Low Effort' },
  MEDIUM: { color: '#eab308', label: 'Med Effort' },
  HIGH: { color: '#ef4444', label: 'High Effort' },
};

function RiskCard({ risk }) {
  const sc = SEVERITY_CONFIG[risk.severity] || SEVERITY_CONFIG.MEDIUM;
  const typeIcon = RISK_TYPE_ICONS[risk.type] || '⚠';

  const riskScore = (risk.probability * risk.impact * 100).toFixed(0);

  return (
    <div className="risk-card" style={{ borderLeftColor: sc.color, background: sc.bg }}>
      <div className="risk-card-header">
        <div className="risk-type-badge">
          <span>{typeIcon}</span>
          <span>{risk.type}</span>
        </div>
        <div className="risk-severity" style={{ color: sc.color }}>
          <span>{sc.icon}</span>
          <span>{risk.severity}</span>
        </div>
        <div className="risk-score">
          <span className="score-label">Risk Score</span>
          <span className="score-value" style={{ color: sc.color }}>{riskScore}</span>
        </div>
      </div>

      <h3 className="risk-title">{risk.title}</h3>
      <p className="risk-desc">{risk.description}</p>

      <div className="risk-meters">
        <div className="meter-item">
          <span className="meter-label">Probability</span>
          <div className="meter-track">
            <div
              className="meter-fill"
              style={{ width: `${risk.probability * 100}%`, background: sc.color }}
            />
          </div>
          <span className="meter-val">{(risk.probability * 100).toFixed(0)}%</span>
        </div>
        <div className="meter-item">
          <span className="meter-label">Impact</span>
          <div className="meter-track">
            <div
              className="meter-fill"
              style={{ width: `${risk.impact * 100}%`, background: sc.color }}
            />
          </div>
          <span className="meter-val">{(risk.impact * 100).toFixed(0)}%</span>
        </div>
      </div>

      {risk.affected_tasks?.length > 0 && (
        <div className="risk-affected">
          <span className="affected-label">Affects:</span>
          {risk.affected_tasks.map((t, i) => (
            <span key={i} className="affected-tag">{t}</span>
          ))}
        </div>
      )}

      <div className="risk-suggestion">
        <span className="suggestion-icon">◈</span>
        <div>
          <div className="suggestion-label">Suggested Action</div>
          <div className="suggestion-text">{risk.suggested_action}</div>
        </div>
      </div>

      {risk.reasoning && (
        <div className="risk-reasoning">
          <span className="reasoning-badge">Agent reasoning:</span>
          <span>{risk.reasoning}</span>
        </div>
      )}
    </div>
  );
}

function ActionCard({ action, index }) {
  const ec = EFFORT_CONFIG[action.effort] || EFFORT_CONFIG.MEDIUM;

  return (
    <div className="action-card">
      <div className="action-number">{String(index + 1).padStart(2, '0')}</div>
      <div className="action-body">
        <div className="action-header">
          <span className="action-priority-badge">P{action.priority}</span>
          <span className="action-effort" style={{ color: ec.color }}>{ec.label}</span>
        </div>
        <p className="action-text">{action.action}</p>
        {action.impact && (
          <div className="action-impact">
            <span className="impact-label">Impact:</span>
            <span>{action.impact}</span>
          </div>
        )}
        {action.reasoning && (
          <div className="action-reasoning">
            <span className="reasoning-badge">Agent reasoning:</span>
            <span>{action.reasoning}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function RiskPanel({ project, risks, actions, onReanalyze, agentThinking }) {
  const sorted = [...risks].sort((a, b) => {
    const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    return (order[a.severity] || 2) - (order[b.severity] || 2);
  });

  const healthConfig = {
    GREEN: { color: '#22c55e', icon: '●', label: 'Healthy' },
    YELLOW: { color: '#eab308', icon: '◉', label: 'At Risk' },
    RED: { color: '#ef4444', icon: '○', label: 'Critical' },
  };
  const hc = healthConfig[project?.health] || healthConfig.GREEN;

  return (
    <div className="risk-panel">
      {/* Health overview */}
      <div className="health-overview" style={{ borderColor: hc.color }}>
        <div className="health-status" style={{ color: hc.color }}>
          <span className="health-icon">{hc.icon}</span>
          <div>
            <div className="health-label">Project Health</div>
            <div className="health-value">{hc.label}</div>
          </div>
        </div>
        <div className="health-reasoning">
          {project?.health_reasoning || 'No health assessment yet.'}
        </div>
        <button
          className="reanalyze-btn"
          onClick={onReanalyze}
          disabled={agentThinking}
        >
          {agentThinking ? (
            <><span className="btn-spinner-sm" /> Analyzing...</>
          ) : (
            <><span>◎</span> Re-analyze</>
          )}
        </button>
      </div>

      <div className="risk-actions-layout">
        {/* Risks column */}
        <div className="risks-col">
          <div className="section-header">
            <h2 className="section-title">
              <span>⚠</span> Risks
              <span className="section-count">{risks.length}</span>
            </h2>
          </div>

          {sorted.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">●</span>
              <p>No risks detected. Project looks healthy!</p>
            </div>
          ) : (
            <div className="risk-list">
              {sorted.map((risk) => (
                <RiskCard key={risk.id} risk={risk} />
              ))}
            </div>
          )}
        </div>

        {/* Actions column */}
        <div className="actions-col">
          <div className="section-header">
            <h2 className="section-title">
              <span>◈</span> Agent Actions
              <span className="section-count">{actions.length}</span>
            </h2>
          </div>

          {actions.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">◎</span>
              <p>No actions recommended yet.</p>
            </div>
          ) : (
            <div className="action-list">
              {actions.map((action, i) => (
                <ActionCard key={action.id} action={action} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
