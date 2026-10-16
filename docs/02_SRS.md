# ProjectPulse — Software Requirements Specification (SRS)

**Project Name:** ProjectPulse  
**Document Code:** SRS-PP-V1.0  
**Domain:** Data Science + Project Management  
**Target Release:** Internship MVP v1.0  
**Status:** Approved  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) describes the complete functional, behavioral, non-functional, and interface requirements for the **ProjectPulse** platform. It provides the definitive technical blueprint for engineers, data scientists, and evaluators building the Minimum Viable Product (MVP).

### 1.2 Scope of the System
ProjectPulse is an intelligent web application combining classical project management mechanisms (projects, tasks, team workloads, budgets, deadlines) with real-time descriptive analytics and predictive data science (Machine Learning delay prediction and prescriptive AI recommendations).

---

## 2. User Roles and Personas

| Role Identifier | Role Name | System Permissions & Responsibilities |
| :--- | :--- | :--- |
| `ROLE_PM` | **Project Manager** | Full read/write access. Can create/edit/archive projects, add and assign tasks, configure milestones, define budgets, trigger ML risk predictions, and review AI recommendations. |
| `ROLE_MEMBER` | **Team Member** | Operational access. Can view assigned projects and tasks, modify task progress status (`To Do`, `In Progress`, `Completed`), and update logged actual hours. |
| `ROLE_ADMIN` | **System Admin / Reviewer** | Administrative and inspection access. Can manage user accounts, inspect system logs, view analytics dashboards across all projects, and audit ML prediction telemetry. |

---

## 3. System Requirements & Execution Environment

### 3.1 Hardware Requirements
- **Development/Host Server:** Minimum 2 CPU cores, 4 GB RAM, 10 GB available SSD storage.
- **Client Machine:** Any standard workstation or laptop with minimum 2 GB RAM capable of running modern web browsers.

### 3.2 Software & Runtime Requirements
- **Operating System:** Platform-agnostic (Windows 10/11, macOS, Linux/Ubuntu 20.04+).
- **Backend Runtime:** Python 3.10+ (FastAPI / Uvicorn framework).
- **Frontend Runtime:** Node.js 18+ LTS (React 18 / Vite / Tailwind CSS).
- **Database:** SQLite 3 (Default local development) / PostgreSQL 14+ (Production compatible).
- **Machine Learning Core:** scikit-learn 1.3+, NumPy 1.24+, pandas 2.0+, joblib 1.3+.
- **Browser Compatibility:** Chrome 100+, Firefox 100+, Edge 100+, Safari 15+.

---

## 4. Functional Requirements (FR)

### 4.1 Project Management Module
- **FR-PM-01 (Create Project):** The system shall allow authorized users (`ROLE_PM`, `ROLE_ADMIN`) to create a project by specifying: `title`, `description`, `start_date`, `deadline`, `budget`, and initial `status` (`Planning`).
- **FR-PM-02 (View Projects):** The system shall list all projects with summary metrics: title, status, deadline, budget utilization, task completion percentage, and risk classification.
- **FR-PM-03 (Update Project):** The system shall allow project managers to update project parameters including deadline, budget, description, and status (`Planning`, `In Progress`, `Completed`, `On Hold`).
- **FR-PM-04 (Milestone Tracking):** The system shall support creating milestones linked to a project, tracking milestone title, target date, and completion status.

### 4.2 Task Management Module
- **FR-TM-01 (Create Task):** The system shall allow creation of tasks associated with a specific project, specifying `title`, `description`, `priority` (`Low`, `Medium`, `High`, `Critical`), `complexity` (`1 - Low`, `2 - Medium`, `3 - High`), `estimated_hours`, `assigned_to` (TeamMember ID), and `has_dependencies` (Boolean).
- **FR-TM-02 (Update Task Status & Hours):** The system shall allow assigned team members and managers to change task status (`To Do`, `In Progress`, `Completed`) and increment/log `actual_hours`.
- **FR-TM-03 (Filter and Sort Tasks):** The system shall allow filtering tasks by project, assignee, priority, status, and complexity.

### 4.3 Team & Workload Module
- **FR-TEAM-01 (Directory Management):** The system shall maintain team member profiles containing `name`, `email`, `role`, and `capacity_hours_per_week` (default: 40 hrs).
- **FR-TEAM-02 (Workload Aggregation):** The system shall calculate individual assigned workload by summing `estimated_hours` (for pending tasks) and comparing against weekly capacity.

### 4.4 Data Analytics Module
- **FR-DA-01 (Project Completion Rate):** The system shall compute project completion percentage using:
  $$\text{Completion \%} = \left(\frac{\text{Completed Tasks}}{\text{Total Tasks}}\right) \times 100$$
- **FR-DA-02 (Budget Utilization):** The system shall calculate:
  $$\text{Budget Utilization \%} = \left(\frac{\text{Actual Budget Spent}}{\text{Total Budget}}\right) \times 100$$
- **FR-DA-03 (Hours Variance):** The system shall calculate variance between total estimated hours and actual hours logged.
- **FR-DA-04 (Project Health Index):** The system shall generate a real-time composite health status (`Good`, `At Risk`, `Critical`) by evaluating progress against elapsed schedule runway and budget consumption.

### 4.5 Machine Learning & Delay Prediction Module
- **FR-ML-01 (Prediction Invocation):** The system shall provide an endpoint `/api/predict-risk` accepting a `project_id` or explicit operational feature vector.
- **FR-ML-02 (Feature Assembly):** The system shall extract real-time project features:
  1. `team_size`
  2. `total_tasks`
  3. `completed_tasks`
  4. `pending_tasks`
  5. `avg_workload` (hours per member)
  6. `estimated_hours`
  7. `actual_hours`
  8. `deadline_days_remaining`
  9. `previous_delays` (count of past late tasks/milestones)
  10. `budget_utilization` (ratio)
  11. `task_complexity` (mean complexity rating)
  12. `dependencies` (count of dependent tasks)
- **FR-ML-03 (Inference Execution):** The system shall feed the feature vector to a serialized Random Forest model and compute:
  - `delay_probability`: Float value $\in [0.00, 1.00]$.
  - `risk_score`: Integer value $\in [0, 100]$.
  - `risk_level`: Enumerated string (`Low`, `Medium`, `High`).
  - `expected_delay_days`: Integer or float representing estimated schedule slippage in days.
- **FR-ML-04 (Prediction Storage):** Every prediction run shall be persisted in the `predictions` table with a timestamp for auditability and trend tracking.

### 4.6 AI Recommendations Module
- **FR-REC-01 (Rule-Based Synthesis):** Upon completing ML risk inference, the system shall evaluate business rules and output targeted recommendations:
  1. **Task Redistribution:** If any team member workload $> 120\%$ capacity and pending tasks exist.
  2. **Critical Task Prioritization:** If pending tasks include $\ge 2$ tasks with `Critical` priority or `High` complexity while deadline $\le 10$ days.
  3. **Workload Reduction:** If `actual_hours` $> 1.15 \times \text{estimated_hours}$ or `avg_workload` $> 45$ hours/member.
  4. **Deadline Monitoring:** If `delay_probability` $> 0.60$ or `risk_score` $> 65$.
  5. **Budget Review:** If `budget_utilization` $> \text{completion\_rate} + 0.15$.

### 4.7 User Authentication & Account Recovery Module
- **FR-AUTH-01 (Strong Password Policy):** The system shall enforce strong passwords during registration and password reset: minimum 8 characters, at least one alphabetic character, and at least one numeric character.
- **FR-AUTH-02 (Forgot Password & OTP Generation):** The system shall allow users to request password recovery. A cryptographically random 6-digit numeric OTP verification code shall be generated with a 10-minute validity window and a maximum limit of 5 verification attempts.
- **FR-AUTH-03 (Account Enumeration Defense):** The recovery request API shall return a generic confirmation message regardless of whether the email exists in the database.
- **FR-AUTH-04 (Secure Reset Token):** Upon successful OTP verification, the system shall issue a single-use 32-byte cryptographic reset token valid for 15 minutes.
- **FR-AUTH-05 (Password Reset & Token Invalidation):** The system shall update the user's password with the new validated password, securely hashed with bcrypt, and immediately invalidate the reset token.

---

## 5. Use Cases

### 5.1 Use Case UC-01: Create and Initialize Project
- **Actor:** Project Manager (`ROLE_PM`)
- **Preconditions:** User is authenticated.
- **Main Flow:**
  1. User navigates to `/projects` and clicks "New Project".
  2. User inputs project title, description, start date, target deadline, and budget.
  3. User submits the form.
  4. Backend validates date constraints (`deadline > start_date`) and positive budget (`budget > 0`).
  5. System records project entity with status `Planning`.
  6. User is redirected to Project Details page.
- **Postconditions:** Project is stored in the database and visible in dashboard listings.

### 5.2 Use Case UC-02: Predict Project Risk and View Recommendations
- **Actor:** Project Manager (`ROLE_PM`)
- **Preconditions:** Project exists with at least 1 task and a defined deadline.
- **Main Flow:**
  1. User opens the Project Details page for an active project.
  2. User clicks the "Assess Risk" button.
  3. Frontend dispatches `POST /api/predict-risk` with `{"project_id": 101}`.
  4. Backend aggregates current project features from database tables (`projects`, `tasks`, `team_members`).
  5. Backend passes structured vector to ML inference engine.
  6. Random Forest model computes delay probability, risk score, and expected delay days.
  7. Recommendation engine executes heuristic evaluation rules.
  8. Backend stores prediction record in `predictions` table and returns JSON response.
  9. Frontend renders Risk Gauge, metrics cards, and recommended action checklist.
- **Alternate Flow (Insufficient Data):**
  - If project has zero tasks, system returns HTTP 422 with message: *"Cannot compute risk for a project with zero tasks. Add at least one task."*

### 5.3 Use Case UC-03: Update Task Status and Actual Hours
- **Actor:** Team Member (`ROLE_MEMBER`)
- **Preconditions:** Task is assigned to the authenticated user.
- **Main Flow:**
  1. User accesses the Tasks screen and opens their assigned task.
  2. User transitions status from `In Progress` to `Completed`.
  3. User logs incremental actual hours (e.g., from 4 to 7 hours).
  4. User clicks "Save".
  5. Backend updates task record and re-computes project analytics.
- **Postconditions:** Task is marked completed; project completion percentage updates instantly.

---

## 6. Non-Functional Requirements (NFR)

### 6.1 Performance
- **NFR-PERF-01:** Standard REST API endpoints (GET/POST/PATCH) shall respond within $150 \text{ ms}$ under normal load ($\le 50$ concurrent requests).
- **NFR-PERF-02:** Machine Learning inference via `/api/predict-risk` shall execute within $200 \text{ ms}$.
- **NFR-PERF-03:** Client-side initial render time shall not exceed $1.5 \text{ seconds}$ on standard broadband connections.

### 6.2 Security
- **NFR-SEC-01 (Authentication):** User sessions managed via stateless JWT (JSON Web Tokens) with standard SHA-256 signatures and expiration controls.
- **NFR-SEC-02 (Password Hashing):** All user credentials shall be stored using industry-standard cryptographic hashing (`bcrypt` with salt rounds $\ge 12$).
- **NFR-SEC-03 (Input Sanitization):** All input parameters must be strictly validated using schema validators (Pydantic / Zod) to prevent SQL injection, cross-site scripting (XSS), and buffer overflows.
- **NFR-SEC-04 (CORS):** Backend CORS configuration shall restrict origins strictly to configured frontend hosts.

### 6.3 Reliability & Data Integrity
- **NFR-REL-01:** Foreign key constraints and transaction cascades must ensure no orphan tasks, milestones, or prediction records exist.
- **NFR-REL-02:** If the ML service encounters a feature parsing anomaly, it must fail gracefully with structured error details rather than unhandled server exceptions.

### 6.4 Usability & Accessibility
- **NFR-USE-01:** UI layout must adopt responsive design principles supporting screen viewports from 768px (tablets) up to 1920px (desktops).
- **NFR-USE-02:** Color coding for risk states must be accompanied by explicit text badges (`Low: Green`, `Medium: Amber`, `High: Red`) to support accessibility.

---

## 7. Inputs and Outputs Summary

| Subsystem | Input Parameters | Output Deliverables |
| :--- | :--- | :--- |
| **Project Management** | Title, description, dates, budget, status | Structured Project entity, updated progress |
| **Task Management** | Title, assignee ID, priority, complexity, hours, status | Task entity, recalculated completion rates |
| **Data Analytics** | Raw project and task records | Completion %, burn rate, hour variance, workload index |
| **ML Risk Engine** | 12 engineered project operational features | Delay probability (0–1), Risk score (0–100), Risk level, Expected delay (days) |
| **AI Recommendations** | Risk score, probability, workload variance, budget ratio | Array of actionable recommendation cards |

---

## 8. Constraints and Assumptions

### 8.1 Constraints
1. **Academic/Internship Scope:** The system is an MVP designed for clarity, maintainability, and clean code principles. External enterprise integrations (Jira, SAP, Slack) are out of scope.
2. **Computational Footprint:** ML model inference must run entirely on standard CPU instances without requiring dedicated GPU infrastructure.
3. **Database Architecture:** Relational schema optimized for SQLite (local execution) and PostgreSQL (production).

### 8.2 Assumptions
1. Every project has a defined target deadline and an initial allocated budget $> 0$.
2. Team members have a standard default availability of 40 hours per work week unless customized.
3. Historical training data provides a representative distribution of balanced, delayed, and over-budget project dynamics.
