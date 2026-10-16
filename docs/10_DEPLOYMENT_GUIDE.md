# ProjectPulse — Deployment & Setup Guide

**Document Code:** DEP-GUIDE-PP-V1.0  
**Target Release:** Internship MVP v1.0  
**Supported Environments:** Local Development (macOS, Linux, Windows) & Cloud Production  
**Status:** Approved  

---

## 1. System Prerequisites

Before running or deploying ProjectPulse, ensure the following runtimes and tools are installed:

- **Python:** Version `3.10` or higher (`python --version`)
- **Node.js:** Version `18.x` or higher LTS (`node --version`)
- **Package Managers:** `pip` (Python) and `npm` (Node.js)
- **Git:** Version `2.30+` (`git --version`)
- **Database Engine:**
  - *Local Development:* Embedded SQLite 3 (included with Python standard library).
  - *Production (Optional):* PostgreSQL 14+ (managed instance e.g., Supabase / Neon / Render Postgres).

---

## 2. Local Environment Setup

### 2.1 Repository Directory Structure
```
ProjectPulse/
├── docs/                 # Architectural and technical documentation
├── backend/              # FastAPI application & ML service
│   ├── app/              # Source code (routers, models, services)
│   ├── ml/               # Training script & serialized model artifact
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Backend environment template
├── frontend/             # React 18 SPA (Vite + Tailwind)
│   ├── src/              # Components, pages, hooks, api client
│   ├── package.json      # Frontend dependencies & scripts
│   └── .env.example      # Frontend environment template
└── README.md             # Project quickstart
```

---

### 2.2 Backend Setup & ML Model Initialization

1. **Navigate to the Backend Directory:**
   ```bash
   cd backend
   ```

2. **Create and Activate a Virtual Environment:**
   - *On macOS/Linux:*
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - *On Windows (PowerShell):*
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```

5. **Generate Synthetic Training Data & Train the Random Forest Model:**
   ```bash
   # Generates training dataset and serializes trained model to backend/ml/model.joblib
   python ml/train_model.py
   ```
   *Expected Output:*
   ```text
   [INFO] Generating synthetic project dataset (N=2000)...
   [INFO] Features extracted: 12. Class balance: 61% on-time, 39% delayed.
   [INFO] Training Random Forest Classifier (100 estimators)...
   [INFO] Holdout evaluation completed. Metrics logged.
   [INFO] Model serialized successfully to backend/ml/model.joblib.
   ```

6. **Seed Initial Database with Demo Projects & Tasks:**
   ```bash
   python app/seed_data.py
   ```

7. **Start the FastAPI Backend Server:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - Swagger / OpenAPI Docs available at: `http://127.0.0.1:8000/docs`
   - Health check available at: `http://127.0.0.1:8000/api/health`

---

### 2.3 Frontend Setup

1. **Open a New Terminal and Navigate to Frontend Directory:**
   ```bash
   cd frontend
   ```

2. **Install Node Packages:**
   ```bash
   npm install
   ```

3. **Configure Frontend Environment Variables:**
   ```bash
   cp .env.example .env
   ```

4. **Start the Development Server:**
   ```bash
   npm run dev
   ```
   - Access the web interface at: `http://localhost:5173`

---

## 3. Environment Variables Configuration

### 3.1 Backend Environment Template (`backend/.env`)
```ini
# Application Mode
APP_ENV=development
DEBUG=True
PORT=8000
HOST=127.0.0.1

# Security & Authentication
# Replace with a cryptographically secure random string in production
SECRET_KEY=change_this_to_a_secure_random_secret_key_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database Configuration
# Local SQLite Default:
DATABASE_URL=sqlite:///./projectpulse.db
# Production PostgreSQL Example:
# DATABASE_URL=postgresql://user:password@host:5432/projectpulse

# CORS Settings (Comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# ML Model Artifact Path
ML_MODEL_PATH=ml/model.joblib
```

### 3.2 Frontend Environment Template (`frontend/.env`)
```ini
# Base URL pointing to the FastAPI backend API
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 4. Production Deployment Guidelines

### 4.1 Production Database Setup (PostgreSQL)
For production environments, transition from SQLite to a managed PostgreSQL database:
1. Provision a PostgreSQL 14+ instance on a cloud provider.
2. Update `DATABASE_URL` in the backend environment:
   ```ini
   DATABASE_URL=postgresql+psycopg2://<db_user>:<db_password>@<db_host>:<db_port>/<db_name>
   ```
3. Run Alembic or SQLAlchemy table creation scripts to initialize schemas.

---

### 4.2 Backend Deployment (Render / Cloud Container / VPS)
To deploy the backend to a cloud host (such as Render, Railway, or an Ubuntu VPS):

1. **Build / Start Command:**
   ```bash
   # Build Command
   pip install -r requirements.txt && python ml/train_model.py

   # Start Command
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```
2. **Environment Variables:** Inject all variables defined in `backend/.env` through the cloud provider's dashboard.
3. **Artifact Persistence:** Ensure `model.joblib` is generated during the build step or bundled within the version control / Docker image.

#### Production Dockerfile Reference (Optional)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Train/verify model artifact during image construction
RUN python ml/train_model.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 4.3 Frontend Deployment (Vercel / Netlify)
1. **Build Step:**
   ```bash
   npm run build
   ```
   This generates optimized static HTML/JS/CSS assets in the `frontend/dist/` directory.
2. **Deploy Configuration:**
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - In the hosting environment settings, define:
     `VITE_API_BASE_URL=https://<your-backend-api-domain>/api`
3. **SPA Routing Configuration:** Ensure single-page routing rewrites are enabled so that all paths redirect to `index.html`.

---

## 5. ML Model Deployment & Startup Verification

In ProjectPulse, the ML model is deployed as an in-memory singleton within the FastAPI application lifecycle:

```python
# Startup Lifecycle Handler in app/main.py
@app.on_event("startup")
def load_ml_model():
    model_path = os.getenv("ML_MODEL_PATH", "ml/model.joblib")
    if not os.path.exists(model_path):
        logger.error(f"ML Model file not found at {model_path}!")
        raise RuntimeError(f"Missing ML artifact at {model_path}. Run ml/train_model.py first.")
    
    app.state.ml_model = joblib.load(model_path)
    logger.info("Random Forest Model artifact loaded successfully into memory.")
```

### Verification Checklist
- [ ] Backend starts without error logs regarding `model.joblib`.
- [ ] Visiting `/api/health` returns `{"status": "healthy", "ml_model_loaded": true}`.
- [ ] Executing a test `POST /api/predict-risk` returns a valid JSON risk payload in $< 200\text{ ms}$.
- [ ] Frontend successfully communicates with backend without CORS errors.
