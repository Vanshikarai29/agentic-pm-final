import React, { useState } from "react";

const EXAMPLE_GOALS = [
  "Build a real-time collaborative document editor with offline support, conflict resolution, and version history",
  "Create an e-commerce platform with inventory management, payment processing, and analytics dashboard",
  "Develop a machine learning pipeline for customer churn prediction with model monitoring",
  "Launch a mobile-first social fitness app with workout tracking, challenges, and leaderboards",
];

export default function GoalInput({ onSubmit, loading }) {
  const [goal, setGoal] = useState("");
  const [focused, setFocused] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (goal.trim().length >= 10) {
      onSubmit(goal.trim());
    }
  };

  // ✅ FIX: renamed from useExample (NOT a hook)
  const handleExampleClick = (example) => {
    setGoal(example);
  };

  return (
    <div className="goal-input-page">
      <div className="goal-hero">
        <div className="goal-hero-glyph">◈</div>
        <h1 className="goal-hero-title">
          What are you
          <br />
          <em>building?</em>
        </h1>
        <p className="goal-hero-sub">
          Describe your project goal. The agent will plan it, track it, and
          predict risks — autonomously.
        </p>
      </div>

      <form className="goal-form" onSubmit={handleSubmit}>
        <div
          className={`goal-textarea-wrap ${focused ? "focused" : ""} ${loading ? "loading" : ""}`}
        >
          <textarea
            className="goal-textarea"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="e.g. Build a SaaS analytics dashboard with real-time data ingestion, user management, and custom reporting..."
            rows={4}
            disabled={loading}
          />

          <div className="textarea-meta">
            <span className={`char-count ${goal.length < 10 ? "warn" : ""}`}>
              {goal.length} / 2000
            </span>
          </div>
        </div>

        <button
          type="submit"
          className={`goal-submit-btn ${loading ? "loading" : ""}`}
          disabled={loading || goal.trim().length < 10}
        >
          {loading ? (
            <>
              <span className="btn-spinner" />
              <span>Agent is planning...</span>
            </>
          ) : (
            <>
              <span className="btn-icon">◈</span>
              <span>Launch Agent</span>
            </>
          )}
        </button>
      </form>

      {!loading && (
        <div className="goal-examples">
          <p className="examples-label">Try an example:</p>
          <div className="examples-grid">
            {EXAMPLE_GOALS.map((eg, i) => (
              <button
                key={i}
                className="example-card"
                onClick={() => handleExampleClick(eg)}
              >
                <span className="example-num">0{i + 1}</span>
                <span className="example-text">{eg}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="goal-agent-info">
        <div className="agent-info-item">
          <span className="info-icon">⬡</span>
          <div>
            <strong>Plans tasks</strong>
            <p>Breaks your goal into prioritized tasks with time estimates</p>
          </div>
        </div>

        <div className="agent-info-item">
          <span className="info-icon">◈</span>
          <div>
            <strong>Detects risks</strong>
            <p>
              Identifies schedule, resource, and dependency risks automatically
            </p>
          </div>
        </div>

        <div className="agent-info-item">
          <span className="info-icon">◎</span>
          <div>
            <strong>Reasons visibly</strong>
            <p>Every decision is explained with a full reasoning trace</p>
          </div>
        </div>
      </div>
    </div>
  );
}
