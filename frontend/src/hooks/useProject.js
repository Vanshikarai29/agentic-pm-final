import { useState, useCallback } from 'react';
import * as api from '../api/client';

export function useProject() {
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [risks, setRisks] = useState([]);
  const [actions, setActions] = useState([]);
  const [reasoning, setReasoning] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [agentThinking, setAgentThinking] = useState(false);
  const [error, setError] = useState(null);
  const [activeStep, setActiveStep] = useState('');

  const clearError = () => setError(null);

  const submitGoal = useCallback(async (goal) => {
    setLoading(true);
    setAgentThinking(true);
    setError(null);
    setActiveStep('🔍 Analyzing goal...');
    try {
      const data = await api.submitGoal(goal);
      setProject(data.project);
      setTasks(data.tasks || []);
      setRisks(data.risks || []);
      setActions(data.actions || []);
      setStats(data.stats || null);
      // Fetch reasoning separately
      const reasoningData = await api.getReasoning(data.project.id);
      setReasoning(reasoningData.steps || []);
      setActiveStep('');
      return data.project;
    } catch (e) {
      setError(e.message);
      setActiveStep('');
    } finally {
      setLoading(false);
      setAgentThinking(false);
    }
  }, []);

  const loadProject = useCallback(async (projectId) => {
    setLoading(true);
    setError(null);
    try {
      const [taskData, riskData, reasoningData, actionsData] = await Promise.all([
        api.getTasks(projectId),
        api.getRisks(projectId),
        api.getReasoning(projectId),
        api.getActions(projectId),
      ]);
      setProject(taskData.project);
      setTasks(taskData.tasks || []);
      setStats(taskData.stats || null);
      setRisks(riskData.risks || []);
      setActions(actionsData || []);
      setReasoning(reasoningData.steps || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateTask = useCallback(async (taskId, status, progress, actualHours) => {
    if (!project) return;
    setAgentThinking(true);
    setActiveStep('📊 Analyzing impact...');
    setError(null);
    try {
      const data = await api.updateTask(project.id, taskId, status, progress, actualHours);
      setProject(data.project);
      setTasks(data.tasks || []);
      setRisks(data.risks || []);
      setActions(data.actions || []);
      setStats(data.stats || null);
      // Refresh reasoning
      const reasoningData = await api.getReasoning(project.id);
      setReasoning(reasoningData.steps || []);
      setActiveStep('');
      return data.impact;
    } catch (e) {
      setError(e.message);
      setActiveStep('');
    } finally {
      setAgentThinking(false);
    }
  }, [project]);

  const reanalyze = useCallback(async () => {
    if (!project) return;
    setAgentThinking(true);
    setActiveStep('🔬 Re-analyzing risks...');
    setError(null);
    try {
      const data = await api.reanalyzeRisks(project.id);
      setRisks(data.risks || []);
      setActions(data.actions || []);
      const reasoningData = await api.getReasoning(project.id);
      setReasoning(reasoningData.steps || []);
      setActiveStep('');
    } catch (e) {
      setError(e.message);
      setActiveStep('');
    } finally {
      setAgentThinking(false);
    }
  }, [project]);

  return {
    project, tasks, risks, actions, reasoning, stats,
    loading, agentThinking, error, activeStep,
    clearError, submitGoal, loadProject, updateTask, reanalyze,
  };
}
