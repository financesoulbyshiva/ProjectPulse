import type {
  Project,
  Task,
  TeamMember,
  AnalyticsData,
  User,
  ProjectStatus,
  TaskStatus,
  TaskPriority,
  WorkloadLevel,
  PredictionRequest,
  PredictionResponse,
  ForgotPasswordResponse,
  VerifyResetCodeResponse,
  ResetPasswordResponse,
  VerifyEmailResponse,
  ResendVerificationResponse,
  AIRiskAnalysisResponse,
  FullAIReportResponse,
  RiskHistoryItem
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper to normalize status strings from backend enum to frontend display format
export const normalizeProjectStatus = (status: string): ProjectStatus => {
  const s = status.toUpperCase().replace(/\s+/g, '_');
  switch (s) {
    case 'ON_TRACK':
      return 'On Track';
    case 'AT_RISK':
      return 'At Risk';
    case 'COMPLETED':
      return 'Completed';
    case 'DELAYED':
      return 'Delayed';
    default:
      return 'On Track';
  }
};

export const denormalizeProjectStatus = (status: ProjectStatus): string => {
  return status.toUpperCase().replace(/\s+/g, '_');
};

export const normalizeTaskStatus = (status: string): TaskStatus => {
  const s = status.toUpperCase().replace(/\s+/g, '_');
  switch (s) {
    case 'TODO':
      return 'To Do';
    case 'IN_PROGRESS':
      return 'In Progress';
    case 'COMPLETED':
      return 'Completed';
    default:
      return 'To Do';
  }
};

export const denormalizeTaskStatus = (status: TaskStatus): string => {
  return status.toUpperCase().replace(/\s+/g, '_');
};

export const normalizeTaskPriority = (prio: string): TaskPriority => {
  const p = prio.toUpperCase();
  switch (p) {
    case 'CRITICAL':
      return 'Critical';
    case 'HIGH':
      return 'High';
    case 'MEDIUM':
      return 'Medium';
    case 'LOW':
      return 'Low';
    default:
      return 'Medium';
  }
};

export const normalizeWorkload = (wl: string): WorkloadLevel => {
  const w = wl.toUpperCase();
  switch (w) {
    case 'HIGH':
      return 'High';
    case 'MEDIUM':
      return 'Medium';
    case 'LOW':
      return 'Low';
    default:
      return 'Medium';
  }
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      // keep statusText
    }
    throw new Error(errorDetail || `HTTP error ${res.status}`);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Health
  health: {
    check: async (): Promise<{ status: string }> => {
      const res = await fetch(`${API_BASE}/api/health`);
      return handleResponse(res);
    },
  },

  // Auth
  auth: {
    login: async (email: string, password?: string): Promise<User> => {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: password || 'password123' }),
      });
      const data = await handleResponse<any>(res);
      return {
        id: String(data.id),
        name: data.name,
        email: data.email,
        role: data.role === 'ROLE_PM' ? 'Project Manager' : 'Team Member',
      };
    },

    register: async (name: string, email: string, password: string, role: string): Promise<User> => {
      const backendRole = role === 'Project Manager' ? 'ROLE_PM' : 'ROLE_MEMBER';
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, role: backendRole }),
      });
      const data = await handleResponse<any>(res);
      return {
        id: String(data.id),
        name: data.name,
        email: data.email,
        role: data.role === 'ROLE_PM' ? 'Project Manager' : 'Team Member',
      };
    },

    forgotPassword: async (email: string): Promise<ForgotPasswordResponse> => {
      const res = await fetch(`${API_BASE}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      return handleResponse<ForgotPasswordResponse>(res);
    },

    verifyResetCode: async (email: string, code: string): Promise<VerifyResetCodeResponse> => {
      const res = await fetch(`${API_BASE}/api/auth/verify-reset-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      });
      return handleResponse<VerifyResetCodeResponse>(res);
    },

    resetPassword: async (reset_token: string, new_password: string): Promise<ResetPasswordResponse> => {
      const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset_token, new_password }),
      });
      return handleResponse<ResetPasswordResponse>(res);
    },

    verifyEmail: async (token: string): Promise<VerifyEmailResponse> => {
      const res = await fetch(`${API_BASE}/api/auth/verify-email?token=${encodeURIComponent(token)}`);
      return handleResponse<VerifyEmailResponse>(res);
    },

    resendVerification: async (email: string): Promise<ResendVerificationResponse> => {
      const res = await fetch(`${API_BASE}/api/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      return handleResponse<ResendVerificationResponse>(res);
    },
  },

  // Projects
  projects: {
    list: async (params?: { status?: string; search?: string }): Promise<Project[]> => {
      const query = new URLSearchParams();
      if (params?.status && params.status !== 'All') query.set('status', params.status);
      if (params?.search) query.set('search', params.search);

      const url = `${API_BASE}/api/projects${query.toString() ? `?${query.toString()}` : ''}`;
      const res = await fetch(url);
      const data = await handleResponse<any[]>(res);

      return data.map((p) => {
        const normStatus = normalizeProjectStatus(p.status);
        const isHigh = normStatus === 'Delayed' || normStatus === 'At Risk';
        return {
          id: String(p.id),
          name: p.name,
          description: p.description || '',
          manager: p.manager_name || 'Project Lead',
          startDate: p.start_date,
          deadline: p.deadline,
          budget: p.budget,
          actualSpent: p.actual_cost || 0,
          progress: p.progress,
          status: normStatus,
          teamSize: p.team_size || (p.team_members ? p.team_members.length : 1),
          teamMembers: p.team_members || [p.manager_name || 'Project Lead'],
          complexity: p.complexity === 'HIGH' ? 'High' : p.complexity === 'LOW' ? 'Low' : 'Medium',
          dependencies: p.dependencies || 0,
          riskSummary: {
            riskLevel: isHigh ? 'HIGH' : 'LOW',
            riskScore: isHigh ? 78 : 25,
            delayProbability: isHigh ? 82 : 18,
            expectedDelay: isHigh ? (normStatus === 'Delayed' ? '7 Days' : '4 Days') : '0 Days',
            lastEvaluated: 'Today, 02:30 PM',
          },
        };
      });
    },

    get: async (id: string): Promise<Project> => {
      const res = await fetch(`${API_BASE}/api/projects/${id}`);
      const p = await handleResponse<any>(res);
      const normStatus = normalizeProjectStatus(p.status);
      const isHigh = normStatus === 'Delayed' || normStatus === 'At Risk';

      return {
        id: String(p.id),
        name: p.name,
        description: p.description || '',
        manager: p.manager_name || 'Project Lead',
        startDate: p.start_date,
        deadline: p.deadline,
        budget: p.budget,
        actualSpent: p.actual_cost || 0,
        progress: p.progress,
        status: normStatus,
        teamSize: p.team_size || (p.team_members ? p.team_members.length : 1),
        teamMembers: p.team_members || [p.manager_name || 'Project Lead'],
        complexity: p.complexity === 'HIGH' ? 'High' : p.complexity === 'LOW' ? 'Low' : 'Medium',
        dependencies: p.dependencies || 0,
        riskSummary: {
          riskLevel: isHigh ? 'HIGH' : 'LOW',
          riskScore: isHigh ? 78 : 25,
          delayProbability: isHigh ? 82 : 18,
          expectedDelay: isHigh ? (normStatus === 'Delayed' ? '7 Days' : '4 Days') : '0 Days',
          lastEvaluated: 'Today, 02:30 PM',
        },
      };
    },

    create: async (payload: {
      name: string;
      description?: string;
      start_date: string;
      deadline: string;
      budget: number;
      status?: string;
      complexity?: string;
      dependencies?: number;
      manager_id?: number;
    }): Promise<Project> => {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...payload,
          status: payload.status ? denormalizeProjectStatus(payload.status as ProjectStatus) : 'ON_TRACK',
          complexity: (payload.complexity || 'MEDIUM').toUpperCase(),
        }),
      });
      const p = await handleResponse<any>(res);
      const normStatus = normalizeProjectStatus(p.status);

      return {
        id: String(p.id),
        name: p.name,
        description: p.description || '',
        manager: p.manager_name || 'Project Lead',
        startDate: p.start_date,
        deadline: p.deadline,
        budget: p.budget,
        actualSpent: p.actual_cost || 0,
        progress: p.progress || 0,
        status: normStatus,
        teamSize: p.team_size || 1,
        teamMembers: p.team_members || ['Project Lead'],
        complexity: p.complexity === 'HIGH' ? 'High' : p.complexity === 'LOW' ? 'Low' : 'Medium',
        dependencies: p.dependencies || 0,
        riskSummary: {
          riskLevel: normStatus === 'At Risk' ? 'HIGH' : 'LOW',
          riskScore: normStatus === 'At Risk' ? 70 : 25,
          delayProbability: normStatus === 'At Risk' ? 75 : 20,
          expectedDelay: normStatus === 'At Risk' ? '3 Days' : '0 Days',
          lastEvaluated: 'Just now',
        },
      };
    },

    update: async (id: string, updates: any): Promise<Project> => {
      const payload: any = { ...updates };
      if (updates.status) payload.status = denormalizeProjectStatus(updates.status);
      if (updates.startDate) {
        payload.start_date = updates.startDate;
        delete payload.startDate;
      }

      const res = await fetch(`${API_BASE}/api/projects/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const p = await handleResponse<any>(res);
      const normStatus = normalizeProjectStatus(p.status);

      return {
        id: String(p.id),
        name: p.name,
        description: p.description || '',
        manager: p.manager_name || 'Project Lead',
        startDate: p.start_date,
        deadline: p.deadline,
        budget: p.budget,
        actualSpent: p.actual_cost || 0,
        progress: p.progress || 0,
        status: normStatus,
        teamSize: p.team_size || 1,
        teamMembers: p.team_members || ['Project Lead'],
        complexity: p.complexity === 'HIGH' ? 'High' : p.complexity === 'LOW' ? 'Low' : 'Medium',
        dependencies: p.dependencies || 0,
        riskSummary: {
          riskLevel: normStatus === 'At Risk' ? 'HIGH' : 'LOW',
          riskScore: normStatus === 'At Risk' ? 75 : 25,
          delayProbability: normStatus === 'At Risk' ? 80 : 20,
          expectedDelay: normStatus === 'At Risk' ? '3 Days' : '0 Days',
          lastEvaluated: 'Just now',
        },
      };
    },

    delete: async (id: string): Promise<void> => {
      const res = await fetch(`${API_BASE}/api/projects/${id}`, {
        method: 'DELETE',
      });
      await handleResponse(res);
    },
  },

  // Tasks
  tasks: {
    list: async (params?: { project_id?: number; status?: string; priority?: string }): Promise<Task[]> => {
      const query = new URLSearchParams();
      if (params?.project_id) query.set('project_id', String(params.project_id));
      if (params?.status && params.status !== 'All') query.set('status', params.status);
      if (params?.priority && params.priority !== 'All') query.set('priority', params.priority);

      const url = `${API_BASE}/api/tasks${query.toString() ? `?${query.toString()}` : ''}`;
      const res = await fetch(url);
      const data = await handleResponse<any[]>(res);

      return data.map((t) => ({
        id: String(t.id),
        projectId: String(t.project_id),
        projectName: t.project_name || 'Project',
        title: t.title,
        description: t.description || '',
        assignedTo: t.assignee_name || 'Unassigned',
        priority: normalizeTaskPriority(t.priority),
        dueDate: t.due_date || '',
        status: normalizeTaskStatus(t.status),
        estimatedHours: t.estimated_hours || 0,
        actualHours: t.actual_hours || 0,
        complexity: 2,
        hasDependencies: false,
      }));
    },

    create: async (taskData: {
      project_id: number;
      title: string;
      description?: string;
      assigned_to?: number;
      priority?: string;
      due_date?: string;
      status?: string;
      estimated_hours?: number;
      actual_hours?: number;
    }): Promise<Task> => {
      const res = await fetch(`${API_BASE}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...taskData,
          status: taskData.status ? denormalizeTaskStatus(taskData.status as TaskStatus) : 'TODO',
          priority: (taskData.priority || 'MEDIUM').toUpperCase(),
        }),
      });
      const t = await handleResponse<any>(res);

      return {
        id: String(t.id),
        projectId: String(t.project_id),
        projectName: t.project_name || 'Project',
        title: t.title,
        description: t.description || '',
        assignedTo: t.assignee_name || 'Unassigned',
        priority: normalizeTaskPriority(t.priority),
        dueDate: t.due_date || '',
        status: normalizeTaskStatus(t.status),
        estimatedHours: t.estimated_hours || 0,
        actualHours: t.actual_hours || 0,
        complexity: 2,
        hasDependencies: false,
      };
    },

    update: async (id: string, updates: any): Promise<Task> => {
      const payload: any = { ...updates };
      if (updates.status) payload.status = denormalizeTaskStatus(updates.status);
      if (updates.priority) payload.priority = updates.priority.toUpperCase();

      const res = await fetch(`${API_BASE}/api/tasks/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const t = await handleResponse<any>(res);

      return {
        id: String(t.id),
        projectId: String(t.project_id),
        projectName: t.project_name || 'Project',
        title: t.title,
        description: t.description || '',
        assignedTo: t.assignee_name || 'Unassigned',
        priority: normalizeTaskPriority(t.priority),
        dueDate: t.due_date || '',
        status: normalizeTaskStatus(t.status),
        estimatedHours: t.estimated_hours || 0,
        actualHours: t.actual_hours || 0,
        complexity: 2,
        hasDependencies: false,
      };
    },

    delete: async (id: string): Promise<void> => {
      const res = await fetch(`${API_BASE}/api/tasks/${id}`, {
        method: 'DELETE',
      });
      await handleResponse(res);
    },
  },

  // Team
  team: {
    list: async (): Promise<TeamMember[]> => {
      const res = await fetch(`${API_BASE}/api/team`);
      const data = await handleResponse<any[]>(res);

      return data.map((tm) => ({
        id: String(tm.id),
        name: tm.name,
        email: tm.email,
        role: tm.role === 'ROLE_PM' ? 'Lead Architect & PM' : 'Engineer',
        activeProjects: tm.active_projects || 0,
        assignedTasks: tm.assigned_tasks || 0,
        completedTasks: tm.completed_tasks || 0,
        workload: normalizeWorkload(tm.workload),
        status: 'Active',
        capacityHours: tm.capacity_hours || 40,
        allocatedHours: tm.allocated_hours || 0,
      }));
    },

    create: async (memberData: { name: string; email: string; role: string }): Promise<TeamMember> => {
      const res = await fetch(`${API_BASE}/api/team`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(memberData),
      });
      const tm = await handleResponse<any>(res);

      return {
        id: String(tm.id),
        name: tm.name,
        email: tm.email,
        role: tm.role,
        activeProjects: 0,
        assignedTasks: 0,
        completedTasks: 0,
        workload: 'Low',
        status: 'Active',
        capacityHours: 40,
        allocatedHours: 0,
      };
    },
  },

  // Analytics
  analytics: {
    get: async (): Promise<AnalyticsData> => {
      const res = await fetch(`${API_BASE}/api/analytics`);
      return handleResponse<AnalyticsData>(res);
    },
  },

  // Predictions (Phase 4 / Phase 5 ML Integration)
  predictions: {
    predictRisk: async (data: PredictionRequest): Promise<PredictionResponse> => {
      const res = await fetch(`${API_BASE}/api/predict-risk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return handleResponse<PredictionResponse>(res);
    },
  },

  // AI Risk Analyst Engine (Phases 2 - 16)
  ai: {
    analyzeProjectRisk: async (projectId: string | number): Promise<AIRiskAnalysisResponse> => {
      const id = String(projectId).replace(/\D/g, '') || String(projectId);
      const res = await fetch(`${API_BASE}/api/projects/${id}/ai-risk-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      return handleResponse<AIRiskAnalysisResponse>(res);
    },

    getProjectAnalysis: async (projectId: string | number): Promise<AIRiskAnalysisResponse> => {
      const id = String(projectId).replace(/\D/g, '') || String(projectId);
      const res = await fetch(`${API_BASE}/api/projects/${id}/ai-risk-analysis`);
      return handleResponse<AIRiskAnalysisResponse>(res);
    },

    getRiskHistory: async (projectId: string | number): Promise<RiskHistoryItem[]> => {
      const id = String(projectId).replace(/\D/g, '') || String(projectId);
      const res = await fetch(`${API_BASE}/api/projects/${id}/risk-history`);
      return handleResponse<RiskHistoryItem[]>(res);
    },

    getAIReport: async (projectId: string | number): Promise<FullAIReportResponse> => {
      const id = String(projectId).replace(/\D/g, '') || String(projectId);
      const res = await fetch(`${API_BASE}/api/projects/${id}/ai-report`);
      return handleResponse<FullAIReportResponse>(res);
    },
  },
};
