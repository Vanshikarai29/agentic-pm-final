import React, { useState, useEffect } from 'react';
import { getPrompts, updatePrompts } from '../api/client';

const PROMPT_META = {
  system_prompt: {
    label: 'System Prompt',
    description: 'Defines the agent\'s core identity and behavior. Applied to every LLM call.',
    icon: '◎',
    color: '#6366f1',
  },
  planner_prompt: {
    label: 'Planner Prompt',
    description: 'Used when decomposing a project goal into tasks. Variable: {goal}',
    icon: '⬡',
    color: '#3b82f6',
  },
  risk_analysis_prompt: {
    label: 'Risk Analysis Prompt',
    description: 'Used to detect risks in the current project state. Many variables available.',
    icon: '◈',
    color: '#f97316',
  },
  action_suggestion_prompt: {
    label: 'Action Suggestion Prompt',
    description: 'Generates prioritized recommendations based on risks.',
    icon: '●',
    color: '#22c55e',
  },
  progress_analysis_prompt: {
    label: 'Progress Analysis Prompt',
    description: 'Analyzes the impact when a task is updated.',
    icon: '◷',
    color: '#8b5cf6',
  },
};

export default function PromptsEditor() {
  const [prompts, setPrompts] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  const [activeKey, setActiveKey] = useState('system_prompt');
  const [localValues, setLocalValues] = useState({});

  useEffect(() => {
    getPrompts()
      .then((data) => {
        setPrompts(data);
        setLocalValues(data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (key, value) => {
    setLocalValues((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await updatePrompts(localValues);
      setPrompts(localValues);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = (key) => {
    setLocalValues((prev) => ({ ...prev, [key]: prompts[key] }));
  };

  const isDirty = JSON.stringify(localValues) !== JSON.stringify(prompts);

  if (loading) return (
    <div className="prompts-loading">
      <span className="loading-icon">◎</span>
      <p>Loading prompts...</p>
    </div>
  );

  return (
    <div className="prompts-editor">
      <div className="prompts-header">
        <div>
          <h2 className="prompts-title">
            <span>◧</span> Prompt Configuration
          </h2>
          <p className="prompts-subtitle">
            Edit any prompt below and click Save. Changes take effect immediately — no server restart needed.
          </p>
        </div>
        <div className="prompts-save-area">
          {isDirty && !saved && (
            <span className="unsaved-badge">● Unsaved changes</span>
          )}
          {saved && (
            <span className="saved-badge">✓ Saved & reloaded</span>
          )}
          <button
            className={`save-btn ${saving ? 'saving' : ''} ${isDirty ? 'dirty' : ''}`}
            onClick={handleSave}
            disabled={saving || !isDirty}
          >
            {saving ? (
              <><span className="btn-spinner-sm" /> Saving...</>
            ) : (
              <><span>◧</span> Save Prompts</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠</span>
          <span>{error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div className="prompts-layout">
        {/* Sidebar */}
        <div className="prompts-sidebar">
          {Object.entries(PROMPT_META).map(([key, meta]) => {
            const isModified = localValues[key] !== prompts[key];
            return (
              <button
                key={key}
                className={`prompt-nav-item ${activeKey === key ? 'active' : ''}`}
                style={activeKey === key ? { borderLeftColor: meta.color } : {}}
                onClick={() => setActiveKey(key)}
              >
                <span className="pnav-icon" style={{ color: meta.color }}>{meta.icon}</span>
                <div className="pnav-text">
                  <div className="pnav-label">{meta.label}</div>
                  {isModified && <div className="pnav-modified">modified</div>}
                </div>
              </button>
            );
          })}
        </div>

        {/* Editor */}
        <div className="prompts-editor-main">
          {activeKey && PROMPT_META[activeKey] && (
            <>
              <div className="prompt-editor-header">
                <div>
                  <h3 className="prompt-editor-title" style={{ color: PROMPT_META[activeKey].color }}>
                    <span>{PROMPT_META[activeKey].icon}</span>
                    {PROMPT_META[activeKey].label}
                  </h3>
                  <p className="prompt-editor-desc">{PROMPT_META[activeKey].description}</p>
                </div>
                <button
                  className="reset-btn"
                  onClick={() => handleReset(activeKey)}
                  disabled={localValues[activeKey] === prompts[activeKey]}
                >
                  ↺ Reset
                </button>
              </div>

              <textarea
                className="prompt-textarea"
                value={localValues[activeKey] || ''}
                onChange={(e) => handleChange(activeKey, e.target.value)}
                rows={20}
                spellCheck={false}
              />

              <div className="prompt-footer">
                <span className="char-count-label">
                  {(localValues[activeKey] || '').length} characters
                </span>
                {localValues[activeKey] !== prompts[activeKey] && (
                  <span className="modified-notice">● Modified (not yet saved)</span>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
