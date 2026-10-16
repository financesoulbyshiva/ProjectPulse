# ProjectPulse Backend Service

**Tagline:** Track. Analyze. Predict. Deliver.  
**Domain:** Data Science + Project Management  
**Component:** REST API & Persistence Layer (Phase 2 MVP)  

---

## 1. Overview

The ProjectPulse backend is a high-performance, asynchronous REST API service built using **FastAPI**, **SQLAlchemy ORM**, and **SQLite**. It serves as the single source of truth for project lifecycles, fine-grained tasks, team rosters, and real-time project analytics.

In Phase 2, all operational metrics and statuses are computed dynamically from real database records without hardcoding or fabricating data.

---

## 2. Technology Stack

- **Runtime & Language:** Python 3.10+ / 3.11+
- **Web Framework:** FastAPI (Asynchronous ASGI)
- **ASGI Server:** Uvicorn
- **ORM & Database:** SQLAlchemy 2.0 with SQLite (`backend/projectpulse.db`)
- **Schema Validation:** Pydantic v2 (Strict typing, email validation)
- **Security:** Cryptographic password hashing with `bcrypt`
- **Environment:** `python-dotenv` for configuration

---

## 3. Project Directory Structure

```
backend/
├── app/
│   ├── __init__.py           # Application package
│   ├── main.py               # FastAPI application entrypoint & middleware
│   ├── database.py           # SQLite engine, sessionmaker, and Base
│   ├── models.py             # SQLAlchemy ORM models (User, Project, Task, Prediction)
│   ├── schemas.py            # Pydantic request and response models
│   ├── crud.py               # Database queries, status & progress calculation
│   │
│   └── routes/
│       ├── __init__.py       # Routes package
│       ├── auth.py           # /api/auth (register, login)
│       ├── projects.py       # /api/projects (CRUD, dynamic progress)
│       ├── tasks.py          # /api/tasks (CRUD, filtering, hours)
│       ├── team.py           # /api/team (roster, workload calculations)
│       └── analytics.py      # /api/analytics (live aggregate KPI metrics)
│
├── seed.py                   # Realistic database seeder script
├── projectpulse.db           # SQLite database file
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Active local environment
└── README.md                 # Technical documentation
```

---

## 4. Setup & Local Installation

### 4.1 Prerequisites
- Python 3.10+ or 3.11+
- Virtual environment (`venv` or `uv`)

### 4.2 Installation Steps
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4.3 Configure Environment Variables
```bash
cp .env.example .env
```
Default configuration:
```ini
DATABASE_URL=sqlite:///./projectpulse.db
FRONTEND_URL=http://localhost:5173
SECRET_KEY=projectpulse_internship_secret_key_2026
ENVIRONMENT=development
```

---

## 5. Database Initialization & Seeding

Run the seed script to initialize tables and populate realistic demo projects and contributors:
```bash
python seed.py
```
This populates:
- **4 Users:** Rahul Sharma (`ROLE_PM`), Sneha Patil (`ROLE_MEMBER`), Amit Verma (`ROLE_MEMBER`), Priya Deshmukh (`ROLE_MEMBER`)
- **4 Projects:** Mobile Application (₹1,20,000), College Management Portal (₹80,000), AI Analytics Platform (₹95,000), Website Redesign (₹45,000)
- **11 Tasks:** Covering different statuses (`TODO`, `IN_PROGRESS`, `COMPLETED`) and priorities.

---

## 6. Running the Server

Start the Uvicorn ASGI server on port 8000:
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- OpenAPI Specification: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/api/health`

---

## 7. REST API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status check |
| `POST` | `/api/auth/register` | Register new user account (bcrypt hashed) |
| `POST` | `/api/auth/login` | Authenticate user credentials |
| `GET` | `/api/projects` | List projects with dynamic progress & team size |
| `POST` | `/api/projects` | Create new project with date & budget validation |
| `GET` | `/api/projects/{id}` | Retrieve project details, tasks, and team |
| `PATCH` | `/api/projects/{id}` | Update project metadata, status, or budget |
| `DELETE` | `/api/projects/{id}` | Cascade delete project and associated tasks |
| `GET` | `/api/tasks` | List tasks (supports `project_id`, `status`, `priority`) |
| `POST` | `/api/tasks` | Create task with non-negative hours validation |
| `PATCH` | `/api/tasks/{id}` | Update task status, hours, or assignee |
| `DELETE` | `/api/tasks/{id}` | Delete task |
| `GET` | `/api/team` | List team members with active workload calculations |
| `POST` | `/api/team` | Register new contributor to organization roster |
| `GET` | `/api/analytics` | Real-time aggregate KPIs derived from database |

---

## 8. Business Logic Specifications

### 8.1 Project Progress
Calculated dynamically based on real task records:
$$\text{progress} = \left(\frac{\text{completed\_tasks}}{\text{total\_tasks}}\right) \times 100$$
If a project has zero tasks, progress is strictly `0.0`.

### 8.2 Project Status Logic
- **`COMPLETED`:** All tasks associated with the project have status `COMPLETED`.
- **`DELAYED`:** Target deadline has passed with uncompleted tasks remaining.
- **`AT_RISK`:** Deadline is within 14 calendar days and progress $< 60\%$ or high-priority tasks are incomplete.
- **`ON_TRACK`:** Default healthy operational trajectory.
