# ProjectPulse — REST API Specification

**Document Code:** API-SPEC-PP-V1.0  
**Target Release:** Internship MVP v1.0  
**Base URL:** `http://localhost:8000/api`  
**Content-Type:** `application/json`  
**Authentication Scheme:** Bearer Token (JWT in `Authorization` header)  
**Status:** Approved  

---

## 1. Authentication & Common Error Format

### 1.1 Authorization Header
Protected endpoints require an `Authorization` header:
```http
Authorization: Bearer <jwt_access_token>
```

### 1.2 Standard Error Response Format
All error responses adhere to a consistent JSON structure:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Project with id 42 does not exist.",
    "details": null
  }
}
```

### 1.3 Standard HTTP Status Codes
- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Invalid request structure or business logic violation.
- `401 Unauthorized`: Missing or invalid JWT token.
- `404 Not Found`: Target resource does not exist.
- `422 Unprocessable Entity`: Request body failed Pydantic schema validation.
- `500 Internal Server Error`: Unexpected server-side failure.

### 1.4 Authentication & Password Recovery Endpoints

#### 1.4.1 POST `/api/auth/register`
- **Purpose:** Create a new user account with strong password validation.
- **Request Body:**
  ```json
  {
    "name": "Rahul Sharma",
    "email": "rahul.sharma@projectpulse.dev",
    "password": "SecurePassword123",
    "role": "ROLE_PM"
  }
  ```
- **Password Rules:** Min 8 chars, at least 1 letter, at least 1 number.
- **Response (`201 Created`):** Returns user profile without password hash.

#### 1.4.2 POST `/api/auth/login`
- **Purpose:** Authenticate credentials using bcrypt verification.
- **Request Body:**
  ```json
  {
    "email": "rahul.sharma@projectpulse.dev",
    "password": "SecurePassword123"
  }
  ```
- **Response (`200 OK`):** Returns user profile on success.

#### 1.4.3 POST `/api/auth/forgot-password`
- **Purpose:** Request 6-digit OTP password reset code.
- **Request Body:**
  ```json
  {
    "email": "rahul.sharma@projectpulse.dev"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "message": "If an account exists for this email, a verification code has been sent."
  }
  ```
- **Security:** Response prevents account enumeration. OTP code expires in 10 minutes.

#### 1.4.4 POST `/api/auth/verify-reset-code`
- **Purpose:** Verify 6-digit OTP code and obtain cryptographic reset token.
- **Request Body:**
  ```json
  {
    "email": "rahul.sharma@projectpulse.dev",
    "code": "482731"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "message": "Code verified successfully.",
    "reset_token": "a1b2c3d4e5f6..."
  }
  ```
- **Security:** Limited to 5 attempts maximum; single-use OTP code.

#### 1.4.5 POST `/api/auth/reset-password`
- **Purpose:** Set new password using single-use reset token.
- **Request Body:**
  ```json
  {
    "reset_token": "a1b2c3d4e5f6...",
    "new_password": "NewSecurePassword2026"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "message": "Password updated successfully."
  }
  ```
- **Security:** Reset token invalidated immediately after update; new password hashed with bcrypt.

---

## 2. Project Endpoints

### 2.1 GET `/api/projects`
- **Purpose:** Retrieve a list of all projects with aggregated progress and risk summaries.
- **Method:** `GET`
- **Headers:** `Authorization: Bearer <token>`
- **Query Parameters:**
  - `status` (optional, string): Filter by status (`Planning`, `In Progress`, `Completed`, `On Hold`).
  - `search` (optional, string): Search query matching project title.

#### Request Example
```http
GET /api/projects?status=In%20Progress HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOi...
```

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Cloud Migration Phase 2",
      "description": "Migrate core microservices to container cluster",
      "status": "In Progress",
      "start_date": "2026-09-01",
      "deadline": "2026-11-30",
      "budget": 25000.0,
      "actual_cost": 14200.0,
      "total_tasks": 24,
      "completed_tasks": 14,
      "completion_percentage": 58.33,
      "latest_risk_score": 68,
      "latest_risk_level": "Medium",
      "created_at": "2026-09-01T09:00:00Z"
    }
  ]
}
```

#### Errors
- `401 Unauthorized`: Token missing or expired.
- `500 Internal Server Error`: Database query error.

---

### 2.2 POST `/api/projects`
- **Purpose:** Create a new project.
- **Method:** `POST`
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`

#### Request Body
```json
{
  "title": "FinTech Payment Gateway Integration",
  "description": "Integrate PCI-DSS compliant checkout workflow",
  "start_date": "2026-10-10",
  "deadline": "2026-12-15",
  "budget": 18000.0
}
```

#### Response Example (`201 Created`)
```json
{
  "success": true,
  "data": {
    "id": 2,
    "title": "FinTech Payment Gateway Integration",
    "description": "Integrate PCI-DSS compliant checkout workflow",
    "status": "Planning",
    "start_date": "2026-10-10",
    "deadline": "2026-12-15",
    "budget": 18000.0,
    "actual_cost": 0.0,
    "created_by": 1,
    "created_at": "2026-10-07T14:30:00Z",
    "updated_at": "2026-10-07T14:30:00Z"
  }
}
```

#### Errors
- `400 Bad Request`: `deadline` must be after `start_date`, or `budget` must be $> 0$.
- `422 Unprocessable Entity`: Validation error in body fields.

---

### 2.3 GET `/api/projects/:id`
- **Purpose:** Retrieve full details for a single project, including milestones, task summary, and recent prediction snapshot.
- **Method:** `GET`
- **Path Parameter:** `id` (integer) - The project ID.

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Cloud Migration Phase 2",
    "description": "Migrate core microservices to container cluster",
    "status": "In Progress",
    "start_date": "2026-09-01",
    "deadline": "2026-11-30",
    "budget": 25000.0,
    "actual_cost": 14200.0,
    "analytics": {
      "total_tasks": 24,
      "completed_tasks": 14,
      "pending_tasks": 10,
      "completion_percentage": 58.33,
      "estimated_hours_total": 320.0,
      "actual_hours_total": 210.0,
      "budget_utilization_ratio": 0.568,
      "health_status": "Good"
    },
    "milestones": [
      {
        "id": 101,
        "title": "Staging Cluster Provisioning",
        "due_date": "2026-10-15",
        "is_completed": true
      }
    ],
    "latest_prediction": {
      "risk_score": 68,
      "risk_level": "Medium",
      "delay_probability": 0.65,
      "expected_delay_days": 5.5,
      "evaluated_at": "2026-10-07T10:15:00Z"
    }
  }
}
```

#### Errors
- `404 Not Found`: Project with requested ID does not exist.

---

### 2.4 PATCH `/api/projects/:id`
- **Purpose:** Partially update project metadata, status, budget, or deadline.
- **Method:** `PATCH`
- **Path Parameter:** `id` (integer)

#### Request Body
```json
{
  "status": "In Progress",
  "actual_cost": 15800.0,
  "deadline": "2026-12-05"
}
```

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Cloud Migration Phase 2",
    "status": "In Progress",
    "deadline": "2026-12-05",
    "budget": 25000.0,
    "actual_cost": 15800.0,
    "updated_at": "2026-10-07T14:45:00Z"
  }
}
```

#### Errors
- `400 Bad Request`: Invalid status transition or negative values.
- `404 Not Found`: Project not found.

---

## 3. Task Endpoints

### 3.1 GET `/api/tasks`
- **Purpose:** List tasks across projects or filtered by specific attributes.
- **Method:** `GET`
- **Query Parameters:**
  - `project_id` (optional, integer): Filter tasks belonging to project.
  - `assigned_to` (optional, integer): Filter tasks assigned to team member.
  - `status` (optional, string): Filter by status (`To Do`, `In Progress`, `Completed`).
  - `priority` (optional, string): Filter by priority (`Low`, `Medium`, `High`, `Critical`).

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": [
    {
      "id": 12,
      "project_id": 1,
      "assigned_to": 3,
      "assigned_to_name": "Bob Chen",
      "title": "Configure Redis Cache Replica",
      "description": "Deploy redis cluster stateful set",
      "priority": "High",
      "status": "In Progress",
      "complexity": 2,
      "estimated_hours": 16.0,
      "actual_hours": 12.0,
      "has_dependencies": true,
      "due_date": "2026-10-20"
    }
  ]
}
```

---

### 3.2 POST `/api/tasks`
- **Purpose:** Create a new task within a project.
- **Method:** `POST`

#### Request Body
```json
{
  "project_id": 1,
  "assigned_to": 3,
  "title": "Setup Ingress TLS Certificates",
  "description": "Generate cert-manager CRDs for domain verification",
  "priority": "Critical",
  "status": "To Do",
  "complexity": 3,
  "estimated_hours": 10.0,
  "has_dependencies": true,
  "due_date": "2026-10-25"
}
```

#### Response Example (`201 Created`)
```json
{
  "success": true,
  "data": {
    "id": 13,
    "project_id": 1,
    "assigned_to": 3,
    "title": "Setup Ingress TLS Certificates",
    "priority": "Critical",
    "status": "To Do",
    "complexity": 3,
    "estimated_hours": 10.0,
    "actual_hours": 0.0,
    "has_dependencies": true,
    "due_date": "2026-10-25",
    "created_at": "2026-10-07T15:00:00Z"
  }
}
```

#### Errors
- `400 Bad Request`: Associated `project_id` does not exist.
- `422 Unprocessable Entity`: Missing title or complexity not in `[1, 2, 3]`.

---

### 3.3 PATCH `/api/tasks/:id`
- **Purpose:** Update task status, hours logged, or assignee.
- **Method:** `PATCH`
- **Path Parameter:** `id` (integer)

#### Request Body
```json
{
  "status": "Completed",
  "actual_hours": 11.5
}
```

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": {
    "id": 13,
    "project_id": 1,
    "title": "Setup Ingress TLS Certificates",
    "status": "Completed",
    "actual_hours": 11.5,
    "updated_at": "2026-10-07T15:10:00Z"
  }
}
```

---

## 4. Team Endpoints

### 4.1 GET `/api/team`
- **Purpose:** Retrieve the list of all team members with their real-time calculated workload.
- **Method:** `GET`

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Sarah Connor",
      "email": "sarah@projectpulse.dev",
      "role_title": "Lead Architect",
      "capacity_hours_per_week": 40.0,
      "assigned_active_hours": 28.0,
      "workload_percentage": 70.0,
      "active_tasks_count": 3,
      "is_overloaded": false
    },
    {
      "id": 3,
      "name": "Bob Chen",
      "email": "bob@projectpulse.dev",
      "role_title": "DevOps Engineer",
      "capacity_hours_per_week": 40.0,
      "assigned_active_hours": 52.0,
      "workload_percentage": 130.0,
      "active_tasks_count": 6,
      "is_overloaded": true
    }
  ]
}
```

---

## 5. Analytics Endpoints

### 5.1 GET `/api/analytics`
- **Purpose:** Retrieve system-wide or project-specific data analytics KPIs.
- **Method:** `GET`
- **Query Parameters:**
  - `project_id` (optional, integer): If omitted, aggregates across all active projects.

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": {
    "total_projects": 4,
    "active_projects": 3,
    "overall_completion_rate": 64.2,
    "hours_summary": {
      "total_estimated_hours": 1240.0,
      "total_actual_hours": 1180.0,
      "hours_variance": -60.0
    },
    "budget_summary": {
      "total_budget": 120000.0,
      "total_spent": 78500.0,
      "utilization_rate": 65.42
    },
    "risk_distribution": {
      "low": 2,
      "medium": 1,
      "high": 0
    },
    "team_workload_average": 82.5
  }
}
```

---

## 6. Machine Learning Endpoints

### 6.1 POST `/api/predict-risk`
- **Purpose:** Trigger the Random Forest ML inference engine to evaluate delay probability, compute risk score, estimate expected delay, and generate prescriptive AI recommendations.
- **Method:** `POST`

#### Request Body Option A (Standard Database Project Evaluation)
```json
{
  "project_id": 1
}
```

#### Request Body Option B (Direct Feature Vector Simulation / What-If Analysis)
```json
{
  "features": {
    "team_size": 4,
    "total_tasks": 24,
    "completed_tasks": 14,
    "pending_tasks": 10,
    "avg_workload": 32.5,
    "estimated_hours": 320.0,
    "actual_hours": 210.0,
    "deadline_days_remaining": 18,
    "previous_delays": 1,
    "budget_utilization": 0.568,
    "task_complexity": 2.2,
    "dependencies": 4
  }
}
```

#### Response Example (`200 OK`)
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "prediction": {
      "delay_probability": 0.68,
      "risk_score": 66,
      "risk_level": "Medium",
      "expected_delay_days": 5.8
    },
    "features_used": {
      "team_size": 4,
      "total_tasks": 24,
      "completed_tasks": 14,
      "pending_tasks": 10,
      "avg_workload": 32.5,
      "estimated_hours": 320.0,
      "actual_hours": 210.0,
      "deadline_days_remaining": 18,
      "previous_delays": 1,
      "budget_utilization": 0.568,
      "task_complexity": 2.2,
      "dependencies": 4
    },
    "recommendations": [
      {
        "type": "REDISTRIBUTE_TASKS",
        "priority": "High",
        "title": "Redistribute Team Workload",
        "description": "Engineer Bob Chen is currently at 130% workload capacity. Reassign pending non-critical tasks to members with surplus bandwidth."
      },
      {
        "type": "PRIORITIZE_CRITICAL_TASKS",
        "priority": "Medium",
        "title": "Focus on 4 Blocking Dependency Tasks",
        "description": "Tasks with dependencies represent 40% of the remaining backlog. Clear upstream blockers to prevent cascading delay."
      },
      {
        "type": "MONITOR_DEADLINE",
        "priority": "Medium",
        "title": "Review 18-Day Delivery Runway",
        "description": "Delay probability is elevated at 68%. Conduct weekly milestone check-ins with stakeholders."
      }
    ],
    "evaluated_at": "2026-10-07T15:05:00Z"
  }
}
```

#### Errors
- `400 Bad Request`: Neither `project_id` nor `features` provided.
- `404 Not Found`: Project with requested ID does not exist.
- `422 Unprocessable Entity`: Project has zero tasks or incomplete timeline data.
- `500 Internal Server Error`: Serialized ML model artifact missing or failed inference.
