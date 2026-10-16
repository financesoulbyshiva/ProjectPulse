import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app import models

client = TestClient(app)

print("=== 1. Health Check ===")
res_health = client.get("/api/health")
print("Health status:", res_health.status_code, res_health.json())
assert res_health.status_code == 200

print("\n=== 2. Projects in Database ===")
res_proj = client.get("/api/projects")
assert res_proj.status_code == 200
projects = res_proj.json()
print(f"Retrieved {len(projects)} projects:")
for p in projects:
    print(f" - ID {p['id']}: {p['name']} (Budget: {p['budget']}, Deadline: {p['deadline']})")

print("\n=== 3. End-to-End Prediction for Project 1 ===")
# Project 1 payload mapped from project 1
payload_p1 = {
    "project_id": 1,
    "team_size": 4,
    "total_tasks": 5,
    "completed_tasks": 2,
    "pending_tasks": 3,
    "avg_workload": 35.0,
    "estimated_hours": 140.0,
    "actual_hours": 80.0,
    "deadline_days_remaining": 15,
    "previous_delays": 0,
    "budget": 500000.0,
    "spent_budget": 180000.0,
    "task_complexity": 2.0,
    "dependencies": 1
}
res1 = client.post("/api/predict-risk", json=payload_p1)
print("Project 1 response code:", res1.status_code)
pred1 = res1.json()
print("Project 1 response:", json.dumps(pred1, indent=2))
assert res1.status_code == 200
assert "delay_probability" in pred1
assert "risk_score" in pred1
assert "risk_level" in pred1
assert "expected_delay_days" in pred1

print("\n=== 4. End-to-End Prediction for Project 2 (Project Switching Test) ===")
# Project 2 with different inputs (higher risk profile: high workload, 3 days left, 3 delays)
payload_p2 = {
    "project_id": 2,
    "team_size": 2,
    "total_tasks": 10,
    "completed_tasks": 1,
    "pending_tasks": 9,
    "avg_workload": 58.0,
    "estimated_hours": 350.0,
    "actual_hours": 310.0,
    "deadline_days_remaining": 3,
    "previous_delays": 3,
    "budget": 350000.0,
    "spent_budget": 320000.0,
    "task_complexity": 2.8,
    "dependencies": 4
}
res2 = client.post("/api/predict-risk", json=payload_p2)
print("Project 2 response code:", res2.status_code)
pred2 = res2.json()
print("Project 2 response:", json.dumps(pred2, indent=2))
assert res2.status_code == 200

# Confirm values are dynamic and differ across projects
print("\n=== Verifying Dynamic Differences Across Projects ===")
print(f"P1 Risk Score: {pred1['risk_score']} vs P2 Risk Score: {pred2['risk_score']}")
print(f"P1 Delay Prob: {pred1['delay_probability']} vs P2 Delay Prob: {pred2['delay_probability']}")
print(f"P1 Risk Level: {pred1['risk_level']} vs P2 Risk Level: {pred2['risk_level']}")
print(f"P1 Exp Delay: {pred1['expected_delay_days']} vs P2 Exp Delay: {pred2['expected_delay_days']}")
assert pred1["risk_score"] != pred2["risk_score"], "Predictions must not be identical across different projects!"
assert pred1["delay_probability"] != pred2["delay_probability"]

print("\n=== 5. Database Persistence Verification ===")
db = SessionLocal()
try:
    p1_records = db.query(models.Prediction).filter(models.Prediction.project_id == 1).all()
    p2_records = db.query(models.Prediction).filter(models.Prediction.project_id == 2).all()
    print(f"Persisted predictions for project 1: {len(p1_records)}")
    print(f"Persisted predictions for project 2: {len(p2_records)}")
    assert len(p1_records) > 0, "Project 1 prediction must be persisted in DB"
    assert len(p2_records) > 0, "Project 2 prediction must be persisted in DB"
    latest_p1 = p1_records[-1]
    print(f"Latest DB record for Project 1: ID={latest_p1.id}, Score={latest_p1.risk_score}, Level={latest_p1.risk_level}, DelayDays={latest_p1.expected_delay_days}")
    assert latest_p1.risk_score == pred1["risk_score"]
    assert latest_p1.risk_level == pred1["risk_level"]
finally:
    db.close()

print("\n=== 6. Error Handling Verification ===")
# Test invalid payload: missing required field
res_err1 = client.post("/api/predict-risk", json={"team_size": -5})
print("Invalid payload response code:", res_err1.status_code)
assert res_err1.status_code == 422

# Test negative budget:
res_err2 = client.post("/api/predict-risk", json={**payload_p1, "budget": -100})
print("Negative budget response code:", res_err2.status_code)
assert res_err2.status_code == 422

# Test task count invariant violation (completed_tasks > total_tasks):
res_err3 = client.post("/api/predict-risk", json={**payload_p1, "total_tasks": 5, "completed_tasks": 10})
print("Invalid task count invariant response code:", res_err3.status_code)
assert res_err3.status_code == 422

print("\nALL 6 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
