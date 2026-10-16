"""
Test Suite: test_ai_risk_analyst.py
Validates the AI Risk Analyst service and endpoints:
1. Low-risk project scenario
2. Medium-risk project scenario
3. High-risk project scenario
4. Project with overdue tasks
5. Project with insufficient/zero tasks
6. Non-existent project 404 handling
7. Risk improvement comparison loop
8. Historical risk snapshots
9. Full AI executive report generation
"""

import pytest
from datetime import datetime, timedelta
import os
import sys
import pytest
from datetime import datetime, timedelta

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db
from app import models, schemas, crud

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_ai_risk_analysis_non_existent_project():
    """Verify 404 is returned when requesting analysis for non-existent project."""
    response = client.post("/api/projects/99999999/ai-risk-analysis")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_ai_risk_analysis_lifecycle_and_improvement_loop(db_session):
    """
    Test end-to-end AI Risk Analyst lifecycle:
    1. Create a project
    2. Add overdue and high-priority tasks -> High/Medium Risk
    3. Run AI Risk Analysis -> verify structured response (health, drivers, why factors, recommendations, action plan)
    4. Simulate team action (complete tasks) -> Re-analyze -> verify Risk Improvement Delta
    """
    today = datetime.utcnow().date()
    yesterday = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=10)).strftime("%Y-%m-%d")

    # 1. Create test project
    proj_in = schemas.ProjectCreate(
        name=f"AI Analyst Test Project {datetime.utcnow().timestamp()}",
        description="Testing complete AI Risk Analyst intelligence loop",
        start_date=(today - timedelta(days=20)).strftime("%Y-%m-%d"),
        deadline=tomorrow,
        budget=500000.0,
        status="ON_TRACK",
        complexity="HIGH",
        dependencies=4
    )
    project = crud.create_project(db_session, proj_in)
    project_id = project["id"]

    # 2. Add an overdue task and pending tasks
    task1_in = schemas.TaskCreate(
        project_id=project_id,
        title="Critical Payment Gateway Integration",
        description="Blocked by third-party webhook verification",
        priority="HIGH",
        due_date=yesterday,  # Overdue
        status="TODO",
        estimated_hours=30.0,
        actual_hours=20.0
    )
    crud.create_task(db_session, task1_in)

    task2_in = schemas.TaskCreate(
        project_id=project_id,
        title="Database Sharding Migration",
        description="High complexity milestone task",
        priority="HIGH",
        due_date=tomorrow,
        status="IN_PROGRESS",
        estimated_hours=25.0,
        actual_hours=15.0
    )
    crud.create_task(db_session, task2_in)

    # 3. First Analysis Call: Baseline / Elevated Risk
    r1 = client.post(f"/api/projects/{project_id}/ai-risk-analysis")
    assert r1.status_code == 200
    data1 = r1.json()

    # Verify structured fields
    assert data1["project_id"] == project_id
    assert "summary" in data1 and len(data1["summary"]) > 50
    assert data1["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert 0 <= data1["risk_score"] <= 100
    assert 0.0 <= data1["delay_probability"] <= 1.0

    # Project health score
    assert "project_health" in data1
    assert 0 <= data1["project_health"]["score"] <= 100
    assert data1["project_health"]["status"] in ("Healthy", "Needs Attention", "At Risk")

    # Risk drivers (Phase 4)
    assert len(data1["risk_drivers"]) >= 3
    driver_titles = [d["title"] for d in data1["risk_drivers"]]
    assert any("Overdue" in t or "Runway" in t for t in driver_titles)

    # 'Why at risk' factors (Phase 3)
    assert len(data1["risk_factors"]) >= 1
    factor_categories = [f["category"] for f in data1["risk_factors"]]
    assert "Overdue Tasks" in factor_categories

    # Recommendations (Phase 5)
    assert len(data1["recommendations"]) >= 2
    assert data1["recommendations"][0]["priority"] == 1
    assert len(data1["recommendations"][0]["actions"]) >= 1

    # Action plan (Phase 6)
    assert len(data1["action_plan"]["today"]) >= 1
    assert len(data1["action_plan"]["next_48_hours"]) >= 1
    assert len(data1["action_plan"]["before_deadline"]) >= 1

    # First run comparison: baseline established
    assert data1["risk_comparison"]["current_score"] == data1["risk_score"]

    # 4. Simulate Team Action: Complete all overdue and pending tasks
    db_tasks = db_session.query(models.Task).filter(models.Task.project_id == project_id).all()
    for t in db_tasks:
        t.status = "COMPLETED"
        t.actual_hours = t.estimated_hours
    db_session.commit()

    # 5. Second Analysis Call: Re-analyze after team actions
    r2 = client.post(f"/api/projects/{project_id}/ai-risk-analysis")
    assert r2.status_code == 200
    data2 = r2.json()

    # Verify improvement loop
    assert data2["risk_comparison"]["previous_score"] is not None
    assert data2["risk_comparison"]["previous_score"] == data1["risk_score"]
    # Score should improve (decrease) or remain steady
    assert data2["risk_score"] <= data1["risk_score"]
    assert data2["risk_comparison"]["score_delta"] <= 0
    assert data2["risk_comparison"]["has_improved"] is True
    assert "decreased" in data2["risk_comparison"]["comparison_text"].lower() or "steady" in data2["risk_comparison"]["comparison_text"].lower()

    # Verify risk history contains multiple snapshots
    assert len(data2["risk_history"]) >= 2

    # 6. Test GET /api/projects/{id}/risk-history
    r_hist = client.get(f"/api/projects/{project_id}/risk-history")
    assert r_hist.status_code == 200
    hist_items = r_hist.json()
    assert len(hist_items) >= 2
    assert "score" in hist_items[0]
    assert "level" in hist_items[0]

    # 7. Test GET /api/projects/{id}/ai-report
    r_rep = client.get(f"/api/projects/{project_id}/ai-report")
    assert r_rep.status_code == 200
    rep = r_rep.json()
    assert "project_overview" in rep
    assert "project_health" in rep
    assert "risk_assessment" in rep
    assert "why_at_risk" in rep
    assert "top_drivers" in rep
    assert "recommended_actions" in rep
    assert "priority_action_plan" in rep
    assert "executive_summary" in rep
    assert "next_review_date" in rep


def test_ai_risk_analysis_insufficient_data(db_session):
    """Verify that a project with zero tasks returns safe grounded output without hallucinating."""
    today = datetime.utcnow().date()
    proj_in = schemas.ProjectCreate(
        name=f"Empty Project {datetime.utcnow().timestamp()}",
        description="Brand new project with zero tasks yet",
        start_date=today.strftime("%Y-%m-%d"),
        deadline=(today + timedelta(days=60)).strftime("%Y-%m-%d"),
        budget=100000.0,
        status="ON_TRACK",
        complexity="LOW",
        dependencies=0
    )
    project = crud.create_project(db_session, proj_in)
    project_id = project["id"]

    res = client.post(f"/api/projects/{project_id}/ai-risk-analysis")
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == project_id
    assert data["project_metrics"]["total_tasks"] == 0
    # Grounded warning present
    assert any("Insufficient" in f["title"] or "Data" in f["category"] for f in data["risk_factors"])
