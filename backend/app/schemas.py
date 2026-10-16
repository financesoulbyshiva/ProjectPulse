import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator, field_validator


# ==========================================
# USER SCHEMAS
# ==========================================
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: Literal["ROLE_ADMIN", "ROLE_PM", "ROLE_MEMBER", "ROLE_ANALYST"] = "ROLE_PM"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    dev_code: Optional[str] = None


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("The verification code is invalid.")
        return v


class VerifyResetCodeResponse(BaseModel):
    message: str
    reset_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        return v


class ResetPasswordResponse(BaseModel):
    message: str


class UserSimple(BaseModel):
    id: int
    name: str
    email: str
    role: str
    job_title: Optional[str] = None
    email_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserSimple):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(UserResponse):
    access_token: str


class UserRoleUpdate(BaseModel):
    role: Literal["ROLE_ADMIN", "ROLE_PM", "ROLE_MEMBER", "ROLE_ANALYST"]


class VerifyEmailResponse(BaseModel):
    message: str
    email: Optional[str] = None
    already_verified: bool = False


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    message: str
    already_verified: bool = False



# ==========================================
# TASK SCHEMAS
# ==========================================
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    due_date: Optional[str] = None
    status: str = Field(default="TODO", description="TODO, IN_PROGRESS, COMPLETED")
    estimated_hours: float = Field(default=0.0, ge=0.0)
    actual_hours: float = Field(default=0.0, ge=0.0)


class TaskCreate(TaskBase):
    project_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0.0)
    actual_hours: Optional[float] = Field(None, ge=0.0)


class TaskResponse(TaskBase):
    id: int
    project_id: int
    project_name: Optional[str] = None
    assignee_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PROJECT SCHEMAS
# ==========================================
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    start_date: str
    deadline: str
    budget: float = Field(..., gt=0.0)
    status: str = Field(default="ON_TRACK", description="ON_TRACK, AT_RISK, COMPLETED, DELAYED")
    complexity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    dependencies: int = Field(default=0, ge=0)
    manager_id: Optional[int] = None


class ProjectCreate(ProjectBase):
    team_member_ids: Optional[List[int]] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    start_date: Optional[str] = None
    deadline: Optional[str] = None
    budget: Optional[float] = Field(None, gt=0.0)
    actual_cost: Optional[float] = Field(None, ge=0.0)
    status: Optional[str] = None
    complexity: Optional[str] = None
    dependencies: Optional[int] = Field(None, ge=0)
    manager_id: Optional[int] = None
    team_member_ids: Optional[List[int]] = None


class ProjectResponse(ProjectBase):
    id: int
    actual_cost: float
    progress: float
    total_tasks: int
    completed_tasks: int
    manager_name: Optional[str] = None
    team_size: int
    team_members: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    tasks: List[TaskResponse]
    team: List[UserSimple]

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# TEAM SCHEMAS
# ==========================================
class TeamMemberCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    role: str = Field(default="Team Member", max_length=100, description="Job title")
    password: str = Field(..., min_length=8, max_length=72)


class TeamMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    active_projects: int
    assigned_tasks: int
    completed_tasks: int
    workload: str  # LOW, MEDIUM, HIGH
    capacity_hours: float
    allocated_hours: float

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ANALYTICS & HEALTH SCHEMAS
# ==========================================
class AnalyticsResponse(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    delayed_projects: int
    total_tasks: int
    completed_tasks: int
    overall_completion: float
    average_project_progress: float
    status_distribution: Dict[str, int]
    hours_summary: Dict[str, float]
    budget_summary: Dict[str, float]


class HealthResponse(BaseModel):
    status: str


# ==========================================
# PREDICTION SCHEMAS
# ==========================================
class PredictionRequest(BaseModel):
    team_size: int = Field(..., ge=0, description="Active team contributors")
    total_tasks: int = Field(..., ge=0, description="Total project tasks")
    completed_tasks: int = Field(..., ge=0, description="Completed tasks")
    pending_tasks: int = Field(..., ge=0, description="Pending / In-progress tasks")
    avg_workload: float = Field(..., ge=0.0, description="Average weekly workload (hours/dev)")
    estimated_hours: float = Field(..., ge=0.0, description="Total planned hours")
    actual_hours: float = Field(..., ge=0.0, description="Cumulative actual logged hours")
    deadline_days_remaining: int = Field(..., ge=0, description="Runway days remaining")
    previous_delays: int = Field(..., ge=0, description="Past delayed deliverables")
    budget: float = Field(..., gt=0.0, description="Project budget in INR (must be > 0)")
    spent_budget: float = Field(..., ge=0.0, description="Cumulative actual spend")
    task_complexity: float = Field(..., ge=1.0, le=3.0, description="Mean task complexity (1.0 to 3.0)")
    dependencies: int = Field(..., ge=0, description="Blocked/dependent task count")
    project_id: Optional[int] = Field(None, description="Optional Project ID for persistence")

    @model_validator(mode="after")
    def validate_task_consistency(self):
        if self.completed_tasks + self.pending_tasks != self.total_tasks:
            raise ValueError(
                f"Task count mismatch: completed_tasks ({self.completed_tasks}) + "
                f"pending_tasks ({self.pending_tasks}) must equal total_tasks ({self.total_tasks})"
            )
        return self


class PredictionResponse(BaseModel):
    delay_probability: float = Field(..., description="Estimated probability of project delay (0.0 to 1.0)")
    risk_score: int = Field(..., ge=0, le=100, description="Composite risk score (0 to 100)")
    risk_level: str = Field(..., description="Risk category: LOW, MEDIUM, or HIGH")
    expected_delay_days: float = Field(..., ge=0.0, description="Estimated calendar days of delay slippage")
    project_id: Optional[int] = Field(None, description="Associated Project ID if persisted")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# AI RISK ANALYST SCHEMAS
# ==========================================
class AIRiskFactor(BaseModel):
    title: str
    impact: str  # HIGH, MEDIUM, LOW
    evidence: str
    category: str


class AIRiskDriver(BaseModel):
    title: str
    severity: str  # HIGH, MEDIUM, LOW
    evidence: str
    contribution_score: int = Field(..., ge=0, le=100)


class AIRecommendation(BaseModel):
    priority: int
    title: str
    reason: str
    actions: List[str]


class AIActionPlan(BaseModel):
    today: List[str]
    next_48_hours: List[str]
    before_deadline: List[str]


class ProjectHealth(BaseModel):
    score: int = Field(..., ge=0, le=100)
    status: str  # "Healthy", "Needs Attention", "At Risk"
    completion_rate: float
    schedule_health: str
    workload_health: str
    budget_health: str


class RiskComparison(BaseModel):
    previous_score: Optional[int] = None
    previous_level: Optional[str] = None
    previous_delay_probability: Optional[float] = None
    previous_expected_delay_days: Optional[float] = None
    current_score: int
    score_delta: int  # Negative means improved
    has_improved: bool
    comparison_text: str


class RiskHistoryItem(BaseModel):
    id: Optional[int] = None
    date: str
    score: int
    level: str
    delay_probability: float
    expected_delay_days: float


class ProjectMetricsSummary(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    completion_rate: float
    days_remaining: int
    team_size: int
    overloaded_members: int
    avg_workload: float
    budget_utilization: float
    hours_variance: float
    dependencies: int


class AIRiskAnalysisResponse(BaseModel):
    project_id: int
    project_name: str
    summary: str
    risk_level: str  # LOW, MEDIUM, HIGH
    risk_score: int
    delay_probability: float
    expected_delay_days: float
    project_health: ProjectHealth
    risk_factors: List[AIRiskFactor]
    risk_drivers: List[AIRiskDriver]
    recommendations: List[AIRecommendation]
    action_plan: AIActionPlan
    risk_comparison: RiskComparison
    risk_history: List[RiskHistoryItem]
    project_metrics: ProjectMetricsSummary
    evaluated_at: str
    model_name: str = "Random Forest Classifier + AI Risk Analyst"
    provider: str = "deterministic"  # "gemini" or "deterministic"
    analysis_mode: str = "deterministic"  # "llm", "deterministic", or "fallback"
    limitations: List[str] = Field(default_factory=list)


class FullAIReportResponse(BaseModel):
    project_overview: Dict[str, Any]
    project_health: ProjectHealth
    risk_assessment: Dict[str, Any]
    why_at_risk: List[AIRiskFactor]
    top_drivers: List[AIRiskDriver]
    delay_prediction: Dict[str, Any]
    team_analysis: Dict[str, Any]
    recommended_actions: List[AIRecommendation]
    priority_action_plan: AIActionPlan
    risk_trend: List[RiskHistoryItem]
    risk_comparison: RiskComparison
    executive_summary: str
    next_review_date: str
    generated_at: str
    provider: str = "deterministic"  # "gemini" or "deterministic"
    analysis_mode: str = "deterministic"  # "llm", "deterministic", or "fallback"
    limitations: List[str] = Field(default_factory=list)


class GeminiExplanationPayload(BaseModel):
    summary: str = Field(..., description="Evidence-based executive summary interpreting current project status and Random Forest risk")
    why_at_risk: List[AIRiskFactor] = Field(default_factory=list, description="Ranked risk friction factors grounded in observed project data")
    risk_drivers: List[AIRiskDriver] = Field(default_factory=list, description="Top operational risk drivers with severity and evidence")
    recommendations: List[AIRecommendation] = Field(default_factory=list, description="Prioritized corrective recommendations")
    action_plan: AIActionPlan = Field(..., description="Actionable checklist partitioned into today, next_48_hours, before_deadline")
    limitations: List[str] = Field(default_factory=list, description="Explicit notices of missing, sparse, or uncertain project data")

