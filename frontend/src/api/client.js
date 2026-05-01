import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

/* ---------------- ERROR HANDLING ---------------- */
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail || err.message || "Unknown error";

    console.error("❌ API Error:", detail); // 🔥 DEBUG ADDED

    return Promise.reject(new Error(detail));
  },
);

/* ---------------- SAFE RESPONSE HANDLER ---------------- */
const extractData = (res) => {
  console.log("📦 API Response:", res?.data); // 🔥 DEBUG ADDED

  if (res?.data?.success && res?.data?.data !== undefined) {
    return res.data.data;
  }
  return res.data;
};

/* ---------------- API CALLS ---------------- */

export const submitGoal = (goal) => {
  console.log("🚀 Submitting goal:", goal); // 🔥 DEBUG
  return api.post("/goal", { goal }).then(extractData);
};

// export const listProjects = () => {
//   console.log("📋 Fetching projects"); // 🔥 DEBUG
//   return api.get("/projects").then(extractData);
// };
export const listProjects = async () => {
  console.log("📋 Fetching projects");

  const res = await api.get("/projects");

  console.log("🔥 RAW AXIOS RESPONSE:");
  console.log(res);

  console.log("🔥 DATA FIELD:");
  console.log(res.data);

  return res.data.data; // FORCE correct backend shape
};

export const getTasks = (projectId) => {
  console.log("👉 getTasks called with projectId:", projectId); // 🔥 IMPORTANT DEBUG

  if (!projectId) {
    console.error("❌ ERROR: projectId is undefined!");
  }

  return api
    .get("/tasks", { params: { project_id: projectId } })
    .then(extractData);
};

export const updateTask = (
  projectId,
  taskId,
  status,
  progress,
  actualHours = 0,
) => {
  console.log("✏️ updateTask:", {
    projectId,
    taskId,
    status,
    progress,
    actualHours,
  });

  return api
    .post("/update", {
      project_id: projectId,
      task_id: taskId,
      status,
      progress,
      actual_hours: actualHours,
    })
    .then(extractData);
};

export const getRisks = (projectId) =>
  api.get("/risks", { params: { project_id: projectId } }).then(extractData);

export const getReasoning = (projectId) =>
  api
    .get("/reasoning", { params: { project_id: projectId } })
    .then(extractData);

export const getActions = (projectId) =>
  api.get("/actions", { params: { project_id: projectId } }).then(extractData);

export const getStats = (projectId) =>
  api.get("/stats", { params: { project_id: projectId } }).then(extractData);

export const getPrompts = () => api.get("/prompts").then(extractData);

export const updatePrompts = (prompts) =>
  api.post("/prompts", { prompts }).then(extractData);

export const reanalyzeRisks = (projectId) =>
  api
    .post("/risks/reanalyze", null, {
      params: { project_id: projectId },
    })
    .then(extractData);
