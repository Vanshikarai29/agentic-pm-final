import React, { useState } from "react";
import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";

/* ---------------- CONFIG ---------------- */

const PRIORITY_CONFIG = {
  CRITICAL: { color: "#ef4444", icon: "◉", label: "CRITICAL" },
  HIGH: { color: "#f97316", icon: "●", label: "HIGH" },
  MEDIUM: { color: "#eab308", icon: "◎", label: "MEDIUM" },
  LOW: { color: "#22c55e", icon: "○", label: "LOW" },
};

const STATUS_CONFIG = {
  pending: { color: "#6b7280", label: "Pending", icon: "○" },
  in_progress: { color: "#3b82f6", label: "In Progress", icon: "◎" },
  blocked: { color: "#ef4444", label: "Blocked", icon: "⊗" },
  completed: { color: "#22c55e", label: "Completed", icon: "●" },
};

/* ---------------- TASK CARD ---------------- */

function TaskCard({ task, onUpdate, disabled }) {
  const [editing, setEditing] = useState(false);
  const [status, setStatus] = useState(task.status);
  const [progress, setProgress] = useState(task.progress ?? 0);
  const [actualHours, setActualHours] = useState(task.actual_hours ?? 0);
  const [saving, setSaving] = useState(false);

  const pc = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.MEDIUM;
  const sc = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;

  const handleSave = async () => {
    setSaving(true);
    try {
      await onUpdate(task.id, status, progress, actualHours);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const isOverdue =
    task.due_date &&
    new Date(task.due_date) < new Date() &&
    task.status !== "completed";

  return (
    <div className={`task-card ${task.status} ${isOverdue ? "overdue" : ""}`}>
      {/* HEADER */}
      <div className="task-card-header">
        <div className="task-priority-badge" style={{ color: pc.color }}>
          <span>{pc.icon}</span>
          <span>{pc.label}</span>
        </div>

        {isOverdue && <span className="overdue-badge">⚠ OVERDUE</span>}

        <div className="task-status-badge" style={{ color: sc.color }}>
          <span>{sc.icon}</span>
          <span>{sc.label}</span>
        </div>
      </div>

      {/* TITLE */}
      <h3 className="task-title">{task.title}</h3>
      {task.description && <p className="task-desc">{task.description}</p>}

      {/* PROGRESS */}
      <div className="progress-bar-wrap">
        <div className="progress-bar-track">
          <div
            className="progress-bar-fill"
            style={{
              width: `${task.progress ?? 0}%`,
              background: pc.color,
            }}
          />
        </div>

        <span className="progress-label">{task.progress ?? 0}%</span>
      </div>

      {/* META */}
      <div className="task-meta">
        <span className="meta-item">
          ⏱ Est: {task.estimated_hours ?? 0}h
          {task.actual_hours > 0 && ` / Act: ${task.actual_hours}h`}
        </span>

        {task.dependencies?.length > 0 && (
          <span className="meta-item">⇢ {task.dependencies.join(", ")}</span>
        )}

        {task.due_date && (
          <span className={`meta-item ${isOverdue ? "overdue-text" : ""}`}>
            ◷ {new Date(task.due_date).toLocaleDateString()}
          </span>
        )}
      </div>

      {/* REASONING */}
      {task.reasoning && (
        <div className="task-reasoning">
          <span>Agent reasoning:</span>
          <span>{task.reasoning}</span>
        </div>
      )}

      {/* EDIT MODE */}
      {editing ? (
        <div className="task-edit-form">
          <div className="edit-row">
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="blocked">Blocked</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div className="edit-row">
            <label>Progress</label>
            <input
              type="range"
              min="0"
              max="100"
              value={progress}
              onChange={(e) => setProgress(Number(e.target.value))}
            />
            <span>{progress}%</span>
          </div>

          <div className="edit-row">
            <label>Actual Hours</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={actualHours}
              onChange={(e) => setActualHours(Number(e.target.value))}
            />
          </div>

          <div className="edit-actions">
            <button onClick={handleSave} disabled={saving || disabled}>
              {saving ? "..." : "✓ Save & Analyze"}
            </button>

            <button onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <button disabled={disabled} onClick={() => setEditing(true)}>
          ◧ Update Progress
        </button>
      )}
    </div>
  );
}

/* ---------------- DASHBOARD ---------------- */

export default function TaskDashboard({
  project,
  tasks,
  stats,
  onUpdateTask,
  agentThinking,
}) {
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("priority");

  const PRIORITY_RANK = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const STATUS_RANK = {
    blocked: 0,
    in_progress: 1,
    pending: 2,
    completed: 3,
  };

  const safeTasks = tasks || [];

  const filtered = safeTasks.filter(
    (t) => filter === "all" || t.status === filter,
  );

  const sorted = [...filtered].sort((a, b) => {
    if (sort === "priority")
      return PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];

    if (sort === "status") return STATUS_RANK[a.status] - STATUS_RANK[b.status];

    if (sort === "progress") return (b.progress ?? 0) - (a.progress ?? 0);

    return 0;
  });

  const chartData = stats
    ? [
        {
          name: "Done",
          value: Number(stats.completion_rate || 0),
          fill: "#22c55e",
        },
      ]
    : [];

  return (
    <div className="task-dashboard">
      {/* STATS */}
      {stats && (
        <div className="stats-row">
          <div className="stat-card">
            <ResponsiveContainer width={80} height={80}>
              <RadialBarChart
                cx="50%"
                cy="50%"
                innerRadius="55%"
                outerRadius="90%"
                data={chartData}
                startAngle={90}
                endAngle={-270}
              >
                <RadialBar dataKey="value" cornerRadius={4} />
              </RadialBarChart>
            </ResponsiveContainer>

            <div>{stats.completion_rate ?? 0}%</div>
          </div>
        </div>
      )}

      {/* FILTERS */}
      <div className="task-controls">
        <div className="filter-group">
          {["all", "pending", "in_progress", "blocked", "completed"].map(
            (f) => (
              <button
                key={f}
                className={filter === f ? "active" : ""}
                onClick={() => setFilter(f)}
              >
                {f === "all" ? "All" : STATUS_CONFIG[f]?.label}
              </button>
            ),
          )}
        </div>

        <div className="sort-group">
          {["priority", "status", "progress"].map((s) => (
            <button
              key={s}
              className={sort === s ? "active" : ""}
              onClick={() => setSort(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* TASKS */}
      <div className="task-grid">
        {sorted.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onUpdate={onUpdateTask}
            disabled={agentThinking}
          />
        ))}
      </div>
    </div>
  );
}
