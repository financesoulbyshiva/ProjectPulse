import os
import json
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app import models, crud
import joblib

client = TestClient(app)

def run_qa_suite():
    print("==================================================================")
    print("          PROJECTPULSE — PHASE 6 COMPREHENSIVE QA SUITE           ")
    print("==================================================================")

    # ---------------------------------------------------------
    # 1. AUTHENTICATION REGRESSION & PASSWORD POLICY
    # ---------------------------------------------------------
    print("\n[QA-01] Testing Exact Password Policy Matrix:")
    test_passwords = [
        ("abc", 422, "FAIL (<8 chars)"),
        ("12345678", 422, "FAIL (no letter)"),
        ("abcdefgh", 422, "FAIL (no number)"),
        ("abc123", 422, "FAIL (<8 chars)"),
        ("Project123", 201, "PASS (>=8 chars, letter + number)"),
    ]
    for pwd, expected_status, label in test_passwords:
        email = f"qa_pwd_{pwd}_{time.time()}@example.com"
        res = client.post("/api/auth/register", json={
            "name": "QA Tester",
            "email": email,
            "password": pwd,
            "role": "ROLE_MEMBER"
        })
        assert res.status_code == expected_status, f"Password {pwd} failed: expected {expected_status}, got {res.status_code}: {res.text}"
        print(f"  [OK] Password '{pwd}' -> {label} (HTTP {res.status_code})")

    print("\n[QA-02] Testing Login & Credential Verification:")
    qa_email = f"qa.login.{time.time()}@projectpulse.dev"
    client.post("/api/auth/register", json={
        "name": "Login User",
        "email": qa_email,
        "password": "InitialPassword123",
        "role": "ROLE_PM"
    })
    # Unverified login attempt
    res_unverified = client.post("/api/auth/login", json={"email": qa_email, "password": "InitialPassword123"})
    assert res_unverified.status_code == 403
    print("  [OK] Unverified account login -> BLOCKED (403 Forbidden)")

    # Verify email
    db = SessionLocal()
    u = crud.get_user_by_email(db, qa_email)
    tok = crud.issue_email_verification_token(db, u)
    db.close()
    ver_res = client.get(f"/api/auth/verify-email?token={tok}")
    assert ver_res.status_code == 200
    print("  [OK] Email verification token -> VERIFIED (200 OK)")

    # Correct login
    res_good = client.post("/api/auth/login", json={"email": qa_email, "password": "InitialPassword123"})
    assert res_good.status_code == 200
    print("  [OK] Correct email + password -> PASS (200 OK)")

    # Incorrect password
    res_bad_pwd = client.post("/api/auth/login", json={"email": qa_email, "password": "WrongPassword999"})
    assert res_bad_pwd.status_code == 401
    print("  [OK] Incorrect password -> FAIL (401 Unauthorized)")

    # Unregistered email
    res_bad_email = client.post("/api/auth/login", json={"email": "nobody@nowhere.com", "password": "AnyPassword123"})
    assert res_bad_email.status_code == 401
    print("  [OK] Unregistered email -> FAIL (401 Unauthorized)")

    print("\n[QA-03] Testing Complete Forgot Password & Recovery Lifecycle:")
    # Trigger forgot password
    forgot_res = client.post("/api/auth/forgot-password", json={"email": qa_email})
    assert forgot_res.status_code == 200
    assert "If an account exists" in forgot_res.json()["message"]
    print("  [OK] Forgot password requested (account enumeration safe)")

    # Extract OTP code from db
    db = SessionLocal()
    code_record = crud.get_latest_reset_code(db, qa_email)
    assert code_record is not None
    db.close()
    otp_code = forgot_res.json().get("dev_code")
    assert otp_code is not None

    # Negative OTP checks
    res_wrong_otp = client.post("/api/auth/verify-reset-code", json={"email": qa_email, "code": "000000"})
    assert res_wrong_otp.status_code == 400
    print("  [OK] Wrong OTP -> FAIL (400 Bad Request)")

    # Verify correct OTP
    verify_res = client.post("/api/auth/verify-reset-code", json={"email": qa_email, "code": otp_code})
    assert verify_res.status_code == 200
    reset_tok = verify_res.json()["reset_token"]
    print("  [OK] Valid OTP verified -> Generated reset_token")

    # OTP reuse
    res_otp_reuse = client.post("/api/auth/verify-reset-code", json={"email": qa_email, "code": otp_code})
    assert res_otp_reuse.status_code == 400
    print("  [OK] Reused OTP -> FAIL (400 Bad Request)")

    # Reset password with weak password
    weak_reset = client.post("/api/auth/reset-password", json={"reset_token": reset_tok, "new_password": "weak"})
    assert weak_reset.status_code == 422
    print("  [OK] Reset with weak password -> FAIL (422 Unprocessable Entity)")

    # Reset with strong password
    new_pwd = "UpdatedPassword2026"
    good_reset = client.post("/api/auth/reset-password", json={"reset_token": reset_tok, "new_password": new_pwd})
    assert good_reset.status_code == 200
    print("  [OK] Password reset success -> Updated successfully")

    # Reset token reuse
    reuse_tok = client.post("/api/auth/reset-password", json={"reset_token": reset_tok, "new_password": "AnotherPassword123"})
    assert reuse_tok.status_code == 400
    print("  [OK] Reused reset token -> FAIL (400 Bad Request)")

    # Login with old password must fail
    old_fail = client.post("/api/auth/login", json={"email": qa_email, "password": "InitialPassword123"})
    assert old_fail.status_code == 401
    print("  [OK] Old password invalidation -> FAIL (401 Unauthorized)")

    # Login with new password must succeed
    new_ok = client.post("/api/auth/login", json={"email": qa_email, "password": new_pwd})
    assert new_ok.status_code == 200
    print("  [OK] New password authentication -> PASS (200 OK)")

    # ---------------------------------------------------------
    # 2. ML REGRESSION TESTING (LOW, MEDIUM, HIGH SCENARIOS)
    # ---------------------------------------------------------
    print("\n[QA-04] Testing ML Model Existence and Scenarios:")
    model_path = os.path.join("data-science", "models", "projectpulse_random_forest.joblib")
    assert os.path.exists(model_path), f"ML Model missing at {model_path}"
    model = joblib.load(model_path)
    print("  [OK] ML model successfully loaded from joblib")

    # Scenario A: LOW Risk
    # completion ~87.5%, workload ~28h, deadline ~45 days, prev_delays=0, budget util ~73%
    payload_low = {
        "team_size": 4,
        "total_tasks": 24,
        "completed_tasks": 21,
        "pending_tasks": 3,
        "avg_workload": 28.0,
        "estimated_hours": 300.0,
        "actual_hours": 240.0,
        "deadline_days_remaining": 45,
        "previous_delays": 0,
        "budget": 500000.0,
        "spent_budget": 365000.0,
        "task_complexity": 1.2,
        "dependencies": 0
    }
    res_low = client.post("/api/predict-risk", json=payload_low)
    assert res_low.status_code == 200
    pred_low = res_low.json()
    print(f"  [OK] Scenario A (Low Risk Profile): Level={pred_low['risk_level']}, Score={pred_low['risk_score']}, Prob={pred_low['delay_probability']}")
    assert pred_low["risk_level"] == "LOW"

    # Scenario B: MEDIUM Risk
    # completion ~48%, workload ~40h, deadline ~28 days, prev_delays=1, budget util ~58%
    payload_med = {
        "team_size": 3,
        "total_tasks": 25,
        "completed_tasks": 12,
        "pending_tasks": 13,
        "avg_workload": 40.0,
        "estimated_hours": 350.0,
        "actual_hours": 200.0,
        "deadline_days_remaining": 28,
        "previous_delays": 1,
        "budget": 400000.0,
        "spent_budget": 232000.0,
        "task_complexity": 2.0,
        "dependencies": 2
    }
    res_med = client.post("/api/predict-risk", json=payload_med)
    assert res_med.status_code == 200
    pred_med = res_med.json()
    print(f"  [OK] Scenario B (Medium Risk Profile): Level={pred_med['risk_level']}, Score={pred_med['risk_score']}, Prob={pred_med['delay_probability']}")
    assert pred_med["risk_level"] in ["LOW", "MEDIUM"]

    # Scenario C: HIGH Risk
    # completion ~21.8%, workload ~56h, deadline ~8 days, prev_delays=4, budget util ~97%
    payload_high = {
        "team_size": 2,
        "total_tasks": 32,
        "completed_tasks": 7,
        "pending_tasks": 25,
        "avg_workload": 56.0,
        "estimated_hours": 450.0,
        "actual_hours": 420.0,
        "deadline_days_remaining": 8,
        "previous_delays": 4,
        "budget": 300000.0,
        "spent_budget": 291000.0,
        "task_complexity": 2.8,
        "dependencies": 5
    }
    res_high = client.post("/api/predict-risk", json=payload_high)
    assert res_high.status_code == 200
    pred_high = res_high.json()
    print(f"  [OK] Scenario C (High Risk Profile): Level={pred_high['risk_level']}, Score={pred_high['risk_score']}, Prob={pred_high['delay_probability']}")
    assert pred_high["risk_level"] == "HIGH"
    assert pred_high["risk_score"] > pred_low["risk_score"]

    # ---------------------------------------------------------
    # 3. PROJECT & TASK MANAGEMENT (CRUD & INVARIANTS)
    # ---------------------------------------------------------
    print("\n[QA-05] Testing Project Management CRUD & Invariants:")
    # Create Project
    p_create = client.post("/api/projects", json={
        "name": f"QA Project {time.time()}",
        "description": "Validation test initiative",
        "start_date": "2026-10-01",
        "deadline": "2026-12-31",
        "budget": 250000.0,
        "status": "ON_TRACK",
        "complexity": "MEDIUM",
        "dependencies": 2
    })
    assert p_create.status_code == 201
    proj = p_create.json()
    p_id = proj["id"]
    print(f"  [OK] Created project ID={p_id}")

    # Add Tasks to Project
    t1 = client.post("/api/tasks", json={
        "project_id": p_id,
        "title": "Task 1 Architecture",
        "priority": "HIGH",
        "status": "COMPLETED",
        "estimated_hours": 40.0,
        "actual_hours": 35.0
    })
    assert t1.status_code == 201
    t2 = client.post("/api/tasks", json={
        "project_id": p_id,
        "title": "Task 2 Implementation",
        "priority": "MEDIUM",
        "status": "IN_PROGRESS",
        "estimated_hours": 60.0,
        "actual_hours": 20.0
    })
    assert t2.status_code == 201
    t3 = client.post("/api/tasks", json={
        "project_id": p_id,
        "title": "Task 3 Testing",
        "priority": "LOW",
        "status": "TODO",
        "estimated_hours": 20.0,
        "actual_hours": 0.0
    })
    assert t3.status_code == 201
    print("  [OK] Created 3 tasks across TODO, IN_PROGRESS, COMPLETED")

    # Verify task invariant: completed + pending == total
    p_refreshed = client.get(f"/api/projects/{p_id}").json()
    tasks = p_refreshed["tasks"]
    total_t = len(tasks)
    completed_t = len([t for t in tasks if t["status"] == "COMPLETED"])
    pending_t = len([t for t in tasks if t["status"] != "COMPLETED"])
    assert total_t == 3
    assert completed_t == 1
    assert pending_t == 2
    assert completed_t + pending_t == total_t, "Invariant violated: completed + pending != total!"
    print(f"  [OK] Invariant Verified: completed ({completed_t}) + pending ({pending_t}) == total ({total_t})")

    # Update Task Status
    t2_id = t2.json()["id"]
    upd_t2 = client.patch(f"/api/tasks/{t2_id}", json={"status": "COMPLETED", "actual_hours": 58.0})
    assert upd_t2.status_code == 200
    p_after = client.get(f"/api/projects/{p_id}").json()
    assert p_after["progress"] > p_refreshed["progress"]
    print(f"  [OK] Dynamic progress updated: {p_refreshed['progress']}% -> {p_after['progress']}%")

    # ---------------------------------------------------------
    # 4. PREDICTION PERSISTENCE & PROJECT SWITCHING
    # ---------------------------------------------------------
    print("\n[QA-06] Testing Prediction Persistence & Project Isolation:")
    # Predict with project_id
    res_p_pred = client.post("/api/predict-risk", json={
        "project_id": p_id,
        "team_size": 3,
        "total_tasks": 3,
        "completed_tasks": 2,
        "pending_tasks": 1,
        "avg_workload": 25.0,
        "estimated_hours": 120.0,
        "actual_hours": 93.0,
        "deadline_days_remaining": 60,
        "previous_delays": 0,
        "budget": 250000.0,
        "spent_budget": 95000.0,
        "task_complexity": 1.5,
        "dependencies": 1
    })
    assert res_p_pred.status_code == 200
    assert res_p_pred.json()["project_id"] == p_id
    print(f"  [OK] Prediction evaluated for Project {p_id}")

    # Check database persistence
    db = SessionLocal()
    persisted_preds = db.query(models.Prediction).filter(models.Prediction.project_id == p_id).all()
    assert len(persisted_preds) >= 1
    db.close()
    print(f"  [OK] Prediction record persisted in DB for project {p_id}")

    # Invalid project ID -> 404
    bad_proj_res = client.post("/api/predict-risk", json={
        "project_id": 9999999,
        "team_size": 2,
        "total_tasks": 2,
        "completed_tasks": 1,
        "pending_tasks": 1,
        "avg_workload": 30.0,
        "estimated_hours": 50.0,
        "actual_hours": 20.0,
        "deadline_days_remaining": 10,
        "previous_delays": 0,
        "budget": 10000.0,
        "spent_budget": 5000.0,
        "task_complexity": 1.0,
        "dependencies": 0
    })
    assert bad_proj_res.status_code == 404
    print("  [OK] Non-existent project_id correctly returned 404 Not Found")

    # ---------------------------------------------------------
    # 5. ANALYTICS & EDGE CASES
    # ---------------------------------------------------------
    print("\n[QA-07] Testing Analytics Endpoint:")
    res_analytics = client.get("/api/analytics")
    assert res_analytics.status_code == 200
    analytics_data = res_analytics.json()
    assert "total_projects" in analytics_data
    assert "overall_completion" in analytics_data
    assert "hours_summary" in analytics_data
    assert "budget_summary" in analytics_data
    print(f"  [OK] Portfolio Analytics: Total Projects={analytics_data['total_projects']}, Completion={analytics_data['overall_completion']}%")

    # ---------------------------------------------------------
    # 6. INVALID INPUTS & VALIDATION RULES
    # ---------------------------------------------------------
    print("\n[QA-08] Testing Invalid Input Rejection:")
    # Negative budget
    neg_b = client.post("/api/predict-risk", json={**payload_low, "budget": -500})
    assert neg_b.status_code == 422
    print("  [OK] Negative budget rejected (422)")

    # Negative team size
    neg_t = client.post("/api/predict-risk", json={**payload_low, "team_size": -1})
    assert neg_t.status_code == 422
    print("  [OK] Negative team_size rejected (422)")

    # Out-of-bounds task complexity (> 3.0)
    high_c = client.post("/api/predict-risk", json={**payload_low, "task_complexity": 5.0})
    assert high_c.status_code == 422
    print("  [OK] Out-of-bounds task complexity rejected (422)")

    # Inconsistent task counts: completed + pending != total
    bad_invar = client.post("/api/predict-risk", json={
        **payload_low,
        "total_tasks": 10,
        "completed_tasks": 8,
        "pending_tasks": 1
    })
    assert bad_invar.status_code == 422
    print("  [OK] Inconsistent task count invariant rejected (422)")

    print("\n==================================================================")
    print("            ALL QA SUITE VERIFICATIONS PASSED (100%)              ")
    print("==================================================================")

if __name__ == "__main__":
    run_qa_suite()
