export type ProjectStatus = 'On Track' | 'At Risk' | 'Completed' | 'Delayed';
export type TaskPriority = 'Low' | 'Medium' | 'High' | 'Critical';
export type TaskStatus = 'To Do' | 'In Progress' | 'Completed';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type WorkloadLevel = 'Low' | 'Medium' | 'High';
export type UserRole = 'Project Manager' | 'Team Member' | 'Data Analyst';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  email_verified?: boolean;
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  activeProjects: number;
  assignedTasks: number;
  completedTasks: number;
  workload: WorkloadLevel;
  status: 'Active' | 'On Leave';
  capacityHours: number;
  allocatedHours: number;
}

export interface ProjectRiskSummary {
  riskLevel: RiskLevel;
  riskScore: number; // 0 - 100
  delayProbability: number; // 0 - 100
  expectedDelay: string; // e.g. "4 Days"
  lastEvaluated: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  manager: string;
  startDate: string;
  deadline: string;
  budget: number; // in INR
  actualSpent: number; // in INR
  progress: number; // 0 - 100
  status: ProjectStatus;
  teamSize: number;
  teamMembers: string[];
  complexity: 'Low' | 'Medium' | 'High';
  dependencies: number;
  riskSummary: ProjectRiskSummary;
}

export interface Task {
  id: string;
  projectId: string;
  projectName: string;
  title: string;
  description?: string;
  assignedTo: string;
  priority: TaskPriority;
  dueDate: string;
  status: TaskStatus;
  estimatedHours: number;
  actualHours: number;
  complexity: 1 | 2 | 3;
  hasDependencies: boolean;
}

export interface PredictionRequest {
  team_size: number;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  avg_workload: number;
  estimated_hours: number;
  actual_hours: number;
  deadline_days_remaining: number;
  previous_delays: number;
  budget: number;
  spent_budget: number;
  task_complexity: number;
  dependencies: number;
  project_id?: number;
}

export interface PredictionResponse {
  delay_probability: number;
  risk_score: number;
  risk_level: RiskLevel;
  expected_delay_days: number;
  project_id?: number;
}

export interface MLPredictionDetails {
  projectId: string;
  projectName: string;
  riskLevel: RiskLevel;
  riskScore: number; // e.g. 78%
  delayProbability: number; // e.g. 82%
  expectedDelay: string; // e.g. "4 Days"
  riskFactors: string[];
  recommendation: string;
  additionalRecommendations?: string[];
  modelName: string;
  evaluatedAt: string;
  isSampleData: boolean;
  inputs: {
    teamSize: number;
    totalTasks: number;
    completedTasks: number;
    pendingTasks: number;
    avgWorkload: number; // hours per member
    estimatedHours: number;
    actualHours: number;
    deadlineDaysRemaining: number;
    previousDelays: number;
    budgetUtilization: number; // percentage
    taskComplexity: number; // 1 - 3 scale
    dependencies: number;
  };
}

export interface ActivityItem {
  id: string;
  user: string;
  action: string;
  target: string;
  timestamp: string;
  type: 'project' | 'task' | 'risk' | 'team';
}

export interface AnalyticsData {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  delayed_projects: number;
  total_tasks: number;
  completed_tasks: number;
  overall_completion: number;
  average_project_progress: number;
  status_distribution: Record<string, number>;
  hours_summary: {
    total_estimated_hours: number;
    total_actual_hours: number;
    hours_variance: number;
  };
  budget_summary: {
    total_budget: number;
    total_spent: number;
    utilization_rate: number;
  };
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
  dev_code?: string;
}

export interface VerifyResetCodeRequest {
  email: string;
  code: string;
}

export interface VerifyResetCodeResponse {
  message: string;
  reset_token: string;
}

export interface ResetPasswordRequest {
  reset_token: string;
  new_password: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface VerifyEmailResponse {
  message: string;
  email?: string;
  already_verified?: boolean;
}

export interface ResendVerificationResponse {
  message: string;
  already_verified?: boolean;
}

export interface AIRiskFactor {
  title: string;
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence: string;
  category: string;
}

export interface AIRiskDriver {
  title: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence: string;
  contribution_score: number;
}

export interface AIRecommendation {
  priority: number;
  title: string;
  reason: string;
  actions: string[];
}

export interface AIActionPlan {
  today: string[];
  next_48_hours: string[];
  before_deadline: string[];
}

export interface ProjectHealth {
  score: number;
  status: 'Healthy' | 'Needs Attention' | 'At Risk';
  completion_rate: number;
  schedule_health: string;
  workload_health: string;
  budget_health: string;
}

export interface RiskComparison {
  previous_score?: number | null;
  previous_level?: string | null;
  previous_delay_probability?: number | null;
  previous_expected_delay_days?: number | null;
  current_score: number;
  score_delta: number;
  has_improved: boolean;
  comparison_text: string;
}

export interface RiskHistoryItem {
  id?: number;
  date: string;
  score: number;
  level: string;
  delay_probability: number;
  expected_delay_days: number;
}

export interface ProjectMetricsSummary {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  days_remaining: number;
  team_size: number;
  overloaded_members: number;
  avg_workload: number;
  budget_utilization: number;
  hours_variance: number;
  dependencies: number;
}

export interface AIRiskAnalysisResponse {
  project_id: number;
  project_name: string;
  summary: string;
  risk_level: RiskLevel;
  risk_score: number;
  delay_probability: number;
  expected_delay_days: number;
  project_health: ProjectHealth;
  risk_factors: AIRiskFactor[];
  risk_drivers: AIRiskDriver[];
  recommendations: AIRecommendation[];
  action_plan: AIActionPlan;
  risk_comparison: RiskComparison;
  risk_history: RiskHistoryItem[];
  project_metrics: ProjectMetricsSummary;
  evaluated_at: string;
  model_name?: string;
}

export interface FullAIReportResponse {
  project_overview: Record<string, any>;
  project_health: ProjectHealth;
  risk_assessment: Record<string, any>;
  why_at_risk: AIRiskFactor[];
  top_drivers: AIRiskDriver[];
  delay_prediction: Record<string, any>;
  team_analysis: Record<string, any>;
  recommended_actions: AIRecommendation[];
  priority_action_plan: AIActionPlan;
  risk_trend: RiskHistoryItem[];
  risk_comparison: RiskComparison;
  executive_summary: string;
  next_review_date: string;
  generated_at: string;
}

