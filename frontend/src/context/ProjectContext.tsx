import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Project, Task, TeamMember, MLPredictionDetails, ActivityItem, TaskStatus, RiskLevel, PredictionRequest, AIRiskAnalysisResponse } from '../types';
import {
  INITIAL_PROJECTS,
  INITIAL_TASKS,
  INITIAL_TEAM_MEMBERS,
  DEMO_PREDICTION_DETAILS,
  INITIAL_ACTIVITIES,
} from '../data/mockData';
import { api } from '../services/api';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ProjectContextType {
  projects: Project[];
  tasks: Task[];
  teamMembers: TeamMember[];
  activities: ActivityItem[];
  toasts: Toast[];
  isLoading: boolean;
  refreshData: () => Promise<void>;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
  addProject: (newProject: Omit<Project, 'id' | 'riskSummary' | 'actualSpent' | 'progress'>) => Promise<Project>;
  updateProject: (id: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  addTask: (newTask: Omit<Task, 'id' | 'actualHours'>) => Promise<Task>;
  updateTaskStatus: (taskId: string, status: TaskStatus) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  addTeamMember: (newMember: Omit<TeamMember, 'id' | 'activeProjects' | 'assignedTasks' | 'completedTasks' | 'allocatedHours'>) => Promise<TeamMember>;
  getProject: (id: string) => Project | undefined;
  getPrediction: (projectId: string) => MLPredictionDetails | undefined;
  predictProjectRisk: (projectId: string) => Promise<MLPredictionDetails>;
  getAIRiskAnalysis: (projectId: string) => AIRiskAnalysisResponse | undefined;
  runAIRiskAnalysis: (projectId: string) => Promise<AIRiskAnalysisResponse>;
  aiAnalysisMap: Record<string, AIRiskAnalysisResponse>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>(INITIAL_TEAM_MEMBERS);
  const [activities, setActivities] = useState<ActivityItem[]>(INITIAL_ACTIVITIES);
  const [predictionsMap, setPredictionsMap] = useState<Record<string, MLPredictionDetails>>({});
  const [aiAnalysisMap, setAiAnalysisMap] = useState<Record<string, AIRiskAnalysisResponse>>({});
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = `toast-${Date.now()}`;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      removeToast(id);
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Initial fetch from backend API
  const refreshData = useCallback(async () => {
    try {
      const [backendProjects, backendTasks, backendTeam] = await Promise.allSettled([
        api.projects.list(),
        api.tasks.list(),
        api.team.list(),
      ]);

      if (backendProjects.status === 'fulfilled' && backendProjects.value.length > 0) {
        setProjects(backendProjects.value);
      }
      if (backendTasks.status === 'fulfilled' && backendTasks.value.length > 0) {
        setTasks(backendTasks.value);
      }
      if (backendTeam.status === 'fulfilled' && backendTeam.value.length > 0) {
        setTeamMembers(backendTeam.value);
      }
    } catch {
      // Fallback to local state if backend is offline
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const addProject = async (projectData: Omit<Project, 'id' | 'riskSummary' | 'actualSpent' | 'progress'>): Promise<Project> => {
    try {
      const created = await api.projects.create({
        name: projectData.name,
        description: projectData.description,
        start_date: projectData.startDate,
        deadline: projectData.deadline,
        budget: projectData.budget,
        status: projectData.status,
        complexity: projectData.complexity,
        dependencies: projectData.dependencies,
      });

      setProjects((prev) => [created, ...prev]);

      const newActivity: ActivityItem = {
        id: `act-${Date.now()}`,
        user: 'You',
        action: 'created new project',
        target: created.name,
        timestamp: 'Just now',
        type: 'project',
      };
      setActivities((prev) => [newActivity, ...prev]);
      showToast(`Project "${created.name}" created successfully.`);
      return created;
    } catch {
      // Offline fallback
      const newId = `proj-${Date.now()}`;
      const initialRiskLevel: RiskLevel = projectData.status === 'At Risk' ? 'HIGH' : 'LOW';
      const fallbackProject: Project = {
        ...projectData,
        id: newId,
        actualSpent: 0,
        progress: 0,
        riskSummary: {
          riskLevel: initialRiskLevel,
          riskScore: initialRiskLevel === 'HIGH' ? 70 : 25,
          delayProbability: initialRiskLevel === 'HIGH' ? 75 : 20,
          expectedDelay: initialRiskLevel === 'HIGH' ? '3 Days' : '0 Days',
          lastEvaluated: 'Just now',
        },
      };

      setProjects((prev) => [fallbackProject, ...prev]);
      showToast(`Project "${fallbackProject.name}" created successfully.`);
      return fallbackProject;
    }
  };

  const updateProject = async (id: string, updates: Partial<Project>) => {
    try {
      const updated = await api.projects.update(id, updates);
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
      showToast('Project updated successfully.');
    } catch {
      setProjects((prev) =>
        prev.map((p) => (p.id === id ? { ...p, ...updates } : p))
      );
      showToast('Project updated successfully.');
    }
  };

  const deleteProject = async (id: string) => {
    try {
      await api.projects.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      setTasks((prev) => prev.filter((t) => t.projectId !== id));
      showToast('Project deleted successfully.');
    } catch {
      setProjects((prev) => prev.filter((p) => p.id !== id));
      showToast('Project deleted successfully.');
    }
  };

  const addTask = async (taskData: Omit<Task, 'id' | 'actualHours'>): Promise<Task> => {
    try {
      // Find matching assignee user ID if numeric
      const member = teamMembers.find((tm) => tm.name === taskData.assignedTo);
      const assigneeId = member ? Number(member.id) : undefined;
      const numProjId = Number(taskData.projectId.replace('proj-', '')) || 1;

      const created = await api.tasks.create({
        project_id: numProjId,
        title: taskData.title,
        description: taskData.description,
        assigned_to: assigneeId,
        priority: taskData.priority,
        due_date: taskData.dueDate,
        status: taskData.status,
        estimated_hours: taskData.estimatedHours,
      });

      setTasks((prev) => [created, ...prev]);
      await refreshData();

      const newActivity: ActivityItem = {
        id: `act-${Date.now()}`,
        user: 'You',
        action: 'added task',
        target: created.title,
        timestamp: 'Just now',
        type: 'task',
      };
      setActivities((prev) => [newActivity, ...prev]);
      showToast(`Task "${created.title}" added successfully.`);
      return created;
    } catch {
      const newId = `tsk-${Date.now()}`;
      const fallbackTask: Task = {
        ...taskData,
        id: newId,
        actualHours: 0,
      };

      setTasks((prev) => [fallbackTask, ...prev]);
      showToast(`Task "${fallbackTask.title}" added successfully.`);
      return fallbackTask;
    }
  };

  const updateTaskStatus = async (taskId: string, status: TaskStatus) => {
    try {
      const updated = await api.tasks.update(taskId, { status });
      setTasks((prev) => prev.map((t) => (t.id === taskId ? updated : t)));
      await refreshData();
      showToast(`Task status updated to ${status}.`);
    } catch {
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status } : t))
      );
      showToast(`Task status updated to ${status}.`);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      await api.tasks.delete(taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      await refreshData();
      showToast('Task removed.');
    } catch {
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      showToast('Task removed.');
    }
  };

  const addTeamMember = async (
    memberData: Omit<TeamMember, 'id' | 'activeProjects' | 'assignedTasks' | 'completedTasks' | 'allocatedHours'>
  ): Promise<TeamMember> => {
    try {
      const created = await api.team.create({
        name: memberData.name,
        email: memberData.email,
        role: memberData.role,
      });
      setTeamMembers((prev) => [...prev, created]);
      showToast(`Team member ${created.name} added to roster.`);
      return created;
    } catch {
      const newId = `tm-${Date.now()}`;
      const fallbackMember: TeamMember = {
        ...memberData,
        id: newId,
        activeProjects: 0,
        assignedTasks: 0,
        completedTasks: 0,
        allocatedHours: 0,
      };
      setTeamMembers((prev) => [...prev, fallbackMember]);
      showToast(`Team member ${fallbackMember.name} added to roster.`);
      return fallbackMember;
    }
  };

  const getProject = (id: string) => {
    return projects.find((p) => p.id === id);
  };

  const getPrediction = (projectId: string): MLPredictionDetails | undefined => {
    if (predictionsMap[projectId]) {
      return predictionsMap[projectId];
    }
    if (DEMO_PREDICTION_DETAILS[projectId]) {
      return DEMO_PREDICTION_DETAILS[projectId];
    }
    const proj = projects.find((p) => p.id === projectId);
    if (!proj) return undefined;

    return {
      projectId: proj.id,
      projectName: proj.name,
      riskLevel: proj.riskSummary.riskLevel,
      riskScore: proj.riskSummary.riskScore,
      delayProbability: proj.riskSummary.delayProbability,
      expectedDelay: proj.riskSummary.expectedDelay,
      riskFactors: [
        `Pending tasks: ${tasks.filter((t) => t.projectId === proj.id && t.status !== 'Completed').length}`,
        `Team size: ${proj.teamSize} contributors`,
        `Dependencies: ${proj.dependencies} registered blocker links`,
      ],
      recommendation: 'Monitor milestones and maintain balanced task allocations.',
      modelName: 'Random Forest Classifier',
      evaluatedAt: proj.riskSummary.lastEvaluated,
      isSampleData: true,
      inputs: {
        teamSize: proj.teamSize,
        totalTasks: tasks.filter((t) => t.projectId === proj.id).length || 5,
        completedTasks: tasks.filter((t) => t.projectId === proj.id && t.status === 'Completed').length || 1,
        pendingTasks: tasks.filter((t) => t.projectId === proj.id && t.status !== 'Completed').length || 4,
        avgWorkload: 35.0,
        estimatedHours: 120,
        actualHours: 85,
        deadlineDaysRemaining: 18,
        previousDelays: 1,
        budgetUtilization: Math.round((proj.actualSpent / proj.budget) * 100),
        taskComplexity: proj.complexity === 'High' ? 2.8 : proj.complexity === 'Medium' ? 2.0 : 1.2,
        dependencies: proj.dependencies,
      },
    };
  };

  const predictProjectRisk = async (projectId: string): Promise<MLPredictionDetails> => {
    const proj = projects.find((p) => p.id === projectId);
    if (!proj) {
      throw new Error(`Project with ID ${projectId} not found.`);
    }

    const projTasks = tasks.filter((t) => t.projectId === proj.id);
    const total_tasks = projTasks.length;
    const completed_tasks = projTasks.filter((t) => t.status === 'Completed').length;
    const pending_tasks = Math.max(0, total_tasks - completed_tasks);

    const team_size = Math.max(proj.teamSize || proj.teamMembers.length || 1, 1);
    const estimated_hours = projTasks.reduce((acc, t) => acc + (t.estimatedHours || 0), 0) || Math.round(proj.budget / 1800) || 120;
    const actual_hours = projTasks.reduce((acc, t) => acc + (t.actualHours || 0), 0) || Math.round((proj.actualSpent || 0) / 1800) || 0;

    const today = new Date();
    const deadlineDate = new Date(proj.deadline);
    const diffDays = Math.ceil((deadlineDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    const deadline_days_remaining = Math.max(1, diffDays > 0 ? diffDays : 2);

    const pendingHours = projTasks
      .filter((t) => t.status !== 'Completed')
      .reduce((acc, t) => acc + (t.estimatedHours || 0), 0);
    const weeksLeft = Math.max(deadline_days_remaining / 7.0, 1.0);
    const rawWorkload = pendingHours > 0 ? (pendingHours / weeksLeft) / team_size : 35.0;
    const avg_workload = Math.round(Math.min(65.0, Math.max(18.0, rawWorkload)) * 10) / 10;

    const overdueCount = projTasks.filter(
      (t) => t.status !== 'Completed' && t.dueDate && new Date(t.dueDate) < today
    ).length;
    const previous_delays = Math.max(
      proj.status === 'Delayed' ? 2 : proj.status === 'At Risk' ? 1 : 0,
      overdueCount
    );

    const budget = Math.max(proj.budget, 1000.0);
    const spent_budget = Math.max(proj.actualSpent || 0.0, 0.0);

    const avgComplexity = projTasks.length > 0
      ? projTasks.reduce((acc, t) => acc + (t.complexity || 2), 0) / projTasks.length
      : proj.complexity === 'High' ? 2.8 : proj.complexity === 'Medium' ? 2.0 : 1.2;
    const task_complexity = Math.round(Math.min(3.0, Math.max(1.0, avgComplexity)) * 10) / 10;

    const depCount = projTasks.filter((t) => t.hasDependencies).length;
    const dependencies = Math.max(proj.dependencies || 0, depCount);

    const rawIdNum = parseInt(proj.id.replace(/\D/g, ''), 10);
    const project_id = Number.isInteger(rawIdNum) && rawIdNum > 0 ? rawIdNum : undefined;

    const payload: PredictionRequest = {
      team_size,
      total_tasks,
      completed_tasks,
      pending_tasks,
      avg_workload,
      estimated_hours,
      actual_hours,
      deadline_days_remaining,
      previous_delays,
      budget,
      spent_budget,
      task_complexity,
      dependencies,
      ...(project_id ? { project_id } : {})
    };

    const res = await api.predictions.predictRisk(payload);

    let recommendation = 'Project is progressing within normal delivery variance. Maintain current execution cadence.';
    let additionalRecommendations: string[] = [
      'Continue regular sprint check-ins.',
      'Maintain balanced developer capacity.',
      'Track deliverables against approved baseline.'
    ];

    if (res.risk_level === 'HIGH') {
      recommendation = 'Critical schedule risk detected. Prioritize overdue and high-complexity tasks, and review deadline feasibility.';
      additionalRecommendations = [
        'Reallocate tasks from overloaded team members.',
        'Resolve blocking dependencies immediately.',
        'Freeze non-essential scope to preserve target delivery.'
      ];
    } else if (res.risk_level === 'MEDIUM') {
      recommendation = 'Moderate schedule strain identified. Monitor pending tasks closely and maintain balanced team allocations.';
      additionalRecommendations = [
        'Review workload distribution across developers.',
        'Track upcoming milestone deadlines weekly.',
        'Address dependencies before they block the critical path.'
      ];
    }

    const factors: string[] = [];
    if (pending_tasks > completed_tasks) {
      factors.push(`High pending backlog (${pending_tasks} remaining of ${total_tasks} total tasks)`);
    }
    if (avg_workload > 40) {
      factors.push(`Elevated team workload (${avg_workload} hrs/member/wk exceeding 40h standard capacity)`);
    }
    if (deadline_days_remaining < 21) {
      factors.push(`Tight runway (${deadline_days_remaining} days remaining until target deadline)`);
    }
    if (previous_delays > 0) {
      factors.push(`Historical delay inertia (${previous_delays} past missed milestone/deadline events)`);
    }
    if ((spent_budget / budget) * 100 > 75 && (completed_tasks / Math.max(total_tasks, 1)) * 100 < 60) {
      factors.push(`Budget burn outrunning completion (${Math.round((spent_budget / budget) * 100)}% budget spent vs ${Math.round((completed_tasks / Math.max(total_tasks, 1)) * 100)}% complete)`);
    }
    if (dependencies > 3) {
      factors.push(`Dependency drag (${dependencies} tasks constrained by predecessor dependencies)`);
    }
    if (factors.length === 0) {
      factors.push('Healthy task throughput with balanced team capacity.');
    }

    const mlDetails: MLPredictionDetails = {
      projectId: proj.id,
      projectName: proj.name,
      riskLevel: res.risk_level,
      riskScore: res.risk_score,
      delayProbability: Math.round(res.delay_probability * 100),
      expectedDelay: `${res.expected_delay_days} Days`,
      riskFactors: factors,
      recommendation,
      additionalRecommendations,
      modelName: 'Random Forest Classifier',
      evaluatedAt: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }),
      isSampleData: false,
      inputs: {
        teamSize: team_size,
        totalTasks: total_tasks,
        completedTasks: completed_tasks,
        pendingTasks: pending_tasks,
        avgWorkload: avg_workload,
        estimatedHours: estimated_hours,
        actualHours: actual_hours,
        deadlineDaysRemaining: deadline_days_remaining,
        previousDelays: previous_delays,
        budgetUtilization: Math.round((spent_budget / budget) * 100),
        taskComplexity: task_complexity,
        dependencies,
      },
    };

    setPredictionsMap((prev) => ({ ...prev, [projectId]: mlDetails }));

    setProjects((prev) =>
      prev.map((p) => {
        if (p.id === proj.id) {
          return {
            ...p,
            riskSummary: {
              riskLevel: res.risk_level,
              riskScore: res.risk_score,
              delayProbability: Math.round(res.delay_probability * 100),
              expectedDelay: `${res.expected_delay_days} Days`,
              lastEvaluated: 'Just now',
            },
          };
        }
        return p;
      })
    );

    return mlDetails;
  };

  const getAIRiskAnalysis = (projectId: string): AIRiskAnalysisResponse | undefined => {
    return aiAnalysisMap[projectId];
  };

  const runAIRiskAnalysis = async (projectId: string): Promise<AIRiskAnalysisResponse> => {
    const rawIdNum = parseInt(projectId.replace(/\D/g, ''), 10);
    const validId = Number.isInteger(rawIdNum) && rawIdNum > 0 ? rawIdNum : 1;
    try {
      const res = await api.ai.analyzeProjectRisk(validId);
      setAiAnalysisMap((prev) => ({ ...prev, [projectId]: res }));

      // Synchronize project's riskSummary in state so the entire UI updates in real-time
      setProjects((prev) =>
        prev.map((p) => {
          if (p.id === projectId) {
            return {
              ...p,
              riskSummary: {
                riskLevel: res.risk_level,
                riskScore: res.risk_score,
                delayProbability: Math.round(res.delay_probability * 100),
                expectedDelay: `${res.expected_delay_days} Days`,
                lastEvaluated: 'Just now',
              },
            };
          }
          return p;
        })
      );

      return res;
    } catch (err: any) {
      showToast(err?.message || 'Failed to complete AI risk analysis', 'error');
      throw err;
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        projects,
        tasks,
        teamMembers,
        activities,
        toasts,
        isLoading,
        refreshData,
        showToast,
        removeToast,
        addProject,
        updateProject,
        deleteProject,
        addTask,
        updateTaskStatus,
        deleteTask,
        addTeamMember,
        getProject,
        getPrediction,
        predictProjectRisk,
        getAIRiskAnalysis,
        runAIRiskAnalysis,
        aiAnalysisMap,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};
