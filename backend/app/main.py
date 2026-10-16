import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import init_db
from .security import validate_security_config
from .routes import auth, projects, tasks, team, analytics, predictions, ai_analysis
from .services.prediction_service import init_ml_model
from . import schemas

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables and ML model are initialized when the server starts."""
    validate_security_config()
    init_db()
    try:
        init_ml_model()
    except Exception as exc:
        print(f"[WARN] ML model warm-up skipped: {exc}")
    yield


app = FastAPI(
    title="ProjectPulse API",
    description="Backend API for ProjectPulse — Track. Analyze. Predict. Deliver.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Setup
frontend_env = os.getenv("FRONTEND_URL", "http://localhost:5173")
configured_origins = [orig.strip().rstrip("/") for orig in frontend_env.split(",") if orig.strip()]

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

origins = list(dict.fromkeys(default_origins + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=schemas.HealthResponse, tags=["Health"])
def health_check():
    """System health check endpoint confirming API service operational status."""
    return {"status": "ok"}


# Include Routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(team.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(ai_analysis.router)
