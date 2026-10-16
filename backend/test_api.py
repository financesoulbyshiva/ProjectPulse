import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.database import SessionLocal, init_db
from app import models, crud

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()


def test_health():
    """Verify system health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_register_and_login():
    """Test user registration, email verification enforcement, and authenticated login."""
    unique_email = f"test.user.{models.datetime.utcnow().timestamp()}@example.com"
    payload = {
        "name": "Test Engineer",
        "email": unique_email,
        "password": "securepassword123",
        "role": "ROLE_PM"
    }

    # Register
    reg_res = client.post("/api/auth/register", json=payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["name"] == "Test Engineer"
    assert user_data["email"] == unique_email
    assert user_data["email_verified"] is False
    assert "password_hash" not in user_data  # Plaintext/hash should not be exposed

    # Unverified login attempt must be rejected with 403 Forbidden
    unverified_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "securepassword123"
    })
    assert unverified_res.status_code == 403
    assert "Please verify your email" in unverified_res.json()["detail"]

    # Verify email via token
    db = SessionLocal()
    user_rec = crud.get_user_by_email(db, unique_email)
    assert user_rec is not None
    assert user_rec.email_verification_token_hash is not None
    assert user_rec.email_verified is False
    raw_token = crud.issue_email_verification_token(db, user_rec)
    db.close()

    verify_res = client.get(f"/api/auth/verify-email?token={raw_token}")
    assert verify_res.status_code == 200
    assert "Email verified successfully" in verify_res.json()["message"]

    # Login after email verification must succeed
    login_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    assert login_res.json()["email"] == unique_email

    # Login with wrong password
    bad_login = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401


def test_auth_duplicate_email():
    """Verify duplicate email registration is rejected with 409 Conflict."""
    email = "rahul.sharma@projectpulse.dev"
    res = client.post("/api/auth/register", json={
        "name": "Rahul Clone",
        "email": email,
        "password": "password123",
        "role": "ROLE_MEMBER"
    })
    assert res.status_code == 409


def test_projects_crud():
    """Verify full Project CRUD lifecycle with validations."""
    # List projects
    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)

    # Create project
    create_payload = {
        "name": "Cloud Native Data Warehouse",
        "description": "Next-gen analytical warehouse on scalable storage",
        "start_date": "2026-10-01",
        "deadline": "2026-12-31",
        "budget": 150000.0,
        "status": "ON_TRACK",
        "complexity": "HIGH",
        "dependencies": 2
    }
    create_res = client.post("/api/projects", json=create_payload)
    assert create_res.status_code == 201
    created_proj = create_res.json()
    proj_id = created_proj["id"]
    assert created_proj["name"] == "Cloud Native Data Warehouse"
    assert created_proj["progress"] == 0.0  # 0 tasks -> 0.0 progress

    # Get project details
    detail_res = client.get(f"/api/projects/{proj_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == proj_id

    # Update project
    update_res = client.patch(f"/api/projects/{proj_id}", json={
        "budget": 160000.0,
        "status": "AT_RISK"
    })
    assert update_res.status_code == 200
    assert update_res.json()["budget"] == 160000.0

    # Negative budget validation
    bad_budget = client.patch(f"/api/projects/{proj_id}", json={"budget": -500})
    assert bad_budget.status_code in (400, 422)

    # Delete project
    del_res = client.delete(f"/api/projects/{proj_id}")
    assert del_res.status_code == 204

    # Verify not found after deletion
    get_after_del = client.get(f"/api/projects/{proj_id}")
    assert get_after_del.status_code == 404


def test_tasks_crud_and_progress_calculation():
    """Verify task creation, updates, and dynamic project progress calculation."""
    # 1. Create a test project
    p_res = client.post("/api/projects", json={
        "name": "Progress Verification Project",
        "description": "Project used for verifying task progress formula",
        "start_date": "2026-10-01",
        "deadline": "2026-11-30",
        "budget": 50000.0,
        "status": "ON_TRACK"
    })
    assert p_res.status_code == 201
    proj_id = p_res.json()["id"]

    # Check initial progress is 0
    p_init = client.get(f"/api/projects/{proj_id}").json()
    assert p_init["progress"] == 0.0

    # 2. Add Task 1 (TODO)
    t1_res = client.post("/api/tasks", json={
        "project_id": proj_id,
        "title": "Task 1",
        "priority": "MEDIUM",
        "status": "TODO",
        "estimated_hours": 10.0,
        "actual_hours": 0.0
    })
    assert t1_res.status_code == 201
    t1_id = t1_res.json()["id"]

    # Progress should still be 0% (0 / 1)
    p_check1 = client.get(f"/api/projects/{proj_id}").json()
    assert p_check1["progress"] == 0.0

    # 3. Add Task 2 (COMPLETED)
    t2_res = client.post("/api/tasks", json={
        "project_id": proj_id,
        "title": "Task 2",
        "priority": "HIGH",
        "status": "COMPLETED",
        "estimated_hours": 15.0,
        "actual_hours": 12.0
    })
    assert t2_res.status_code == 201

    # Progress should now be 50.0% (1 completed out of 2 total)
    p_check2 = client.get(f"/api/projects/{proj_id}").json()
    assert p_check2["progress"] == 50.0

    # 4. Update Task 1 to COMPLETED
    patch_t1 = client.patch(f"/api/tasks/{t1_id}", json={"status": "COMPLETED"})
    assert patch_t1.status_code == 200

    # Progress should now be 100.0% (2 / 2) and status COMPLETED
    p_check3 = client.get(f"/api/projects/{proj_id}").json()
    assert p_check3["progress"] == 100.0
    assert p_check3["status"] == "COMPLETED"

    # Cleanup project
    client.delete(f"/api/projects/{proj_id}")


def test_team_endpoint():
    """Verify team list and workload calculations."""
    res = client.get("/api/team")
    assert res.status_code == 200
    team = res.json()
    assert len(team) >= 4
    for member in team:
        assert "workload" in member
        assert member["workload"] in ("LOW", "MEDIUM", "HIGH")
        assert "allocated_hours" in member


def test_analytics_endpoint():
    """Verify analytics endpoint computes metrics dynamically from the database."""
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_projects"] >= 4
    assert data["total_tasks"] >= 10
    assert "overall_completion" in data
    assert "status_distribution" in data
    assert "budget_summary" in data
    assert data["budget_summary"]["total_budget"] > 0


# ==========================================
# PHASE 4 — PREDICTION API TESTS
# ==========================================
def test_predict_risk_low_risk():
    """Test 1: Verify realistic low-risk project prediction."""
    payload = {
        "team_size": 5,
        "total_tasks": 40,
        "completed_tasks": 35,
        "pending_tasks": 5,
        "avg_workload": 28.0,
        "estimated_hours": 500.0,
        "actual_hours": 300.0,
        "deadline_days_remaining": 45,
        "previous_delays": 0,
        "budget": 1500000.0,
        "spent_budget": 1100000.0,
        "task_complexity": 1.0,
        "dependencies": 2
    }
    res = client.post("/api/predict-risk", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "delay_probability" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "expected_delay_days" in data
    assert 0.0 <= data["delay_probability"] <= 1.0
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert data["expected_delay_days"] >= 0.0


def test_predict_risk_high_risk():
    """Test 2: Verify realistic high-risk project prediction."""
    payload = {
        "team_size": 5,
        "total_tasks": 55,
        "completed_tasks": 12,
        "pending_tasks": 43,
        "avg_workload": 56.0,
        "estimated_hours": 500.0,
        "actual_hours": 450.0,
        "deadline_days_remaining": 8,
        "previous_delays": 4,
        "budget": 1600000.0,
        "spent_budget": 1550000.0,
        "task_complexity": 3.0,
        "dependencies": 10
    }
    res = client.post("/api/predict-risk", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "delay_probability" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "expected_delay_days" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_predict_risk_invalid_negative_value():
    """Test 3: Reject negative numeric inputs with 422."""
    payload = {
        "team_size": -1,
        "total_tasks": 40,
        "completed_tasks": 20,
        "pending_tasks": 20,
        "avg_workload": 30.0,
        "estimated_hours": 400.0,
        "actual_hours": 200.0,
        "deadline_days_remaining": 20,
        "previous_delays": 0,
        "budget": 1000000.0,
        "spent_budget": 500000.0,
        "task_complexity": 2.0,
        "dependencies": 2
    }
    res = client.post("/api/predict-risk", json=payload)
    assert res.status_code == 422


def test_predict_risk_invalid_complexity():
    """Test 4: Reject task complexity > 3 with 422."""
    payload = {
        "team_size": 5,
        "total_tasks": 40,
        "completed_tasks": 20,
        "pending_tasks": 20,
        "avg_workload": 30.0,
        "estimated_hours": 400.0,
        "actual_hours": 200.0,
        "deadline_days_remaining": 20,
        "previous_delays": 0,
        "budget": 1000000.0,
        "spent_budget": 500000.0,
        "task_complexity": 5.0,
        "dependencies": 2
    }
    res = client.post("/api/predict-risk", json=payload)
    assert res.status_code == 422


def test_predict_risk_invalid_task_counts():
    """Test 5: Reject task count inconsistency (completed + pending != total) with 422."""
    payload = {
        "team_size": 5,
        "total_tasks": 40,
        "completed_tasks": 30,
        "pending_tasks": 5,  # 30 + 5 = 35 != 40
        "avg_workload": 30.0,
        "estimated_hours": 400.0,
        "actual_hours": 200.0,
        "deadline_days_remaining": 20,
        "previous_delays": 0,
        "budget": 1000000.0,
        "spent_budget": 500000.0,
        "task_complexity": 2.0,
        "dependencies": 2
    }
    res = client.post("/api/predict-risk", json=payload)
    assert res.status_code == 422


def test_predict_risk_model_reload():
    """Test 6: Verify model artifact loads and functions via service."""
    from app.services.prediction_service import init_ml_model, get_risk_prediction
    model_artifact = init_ml_model()
    assert model_artifact is not None
    assert "model" in model_artifact

    pred = get_risk_prediction({
        "team_size": 4,
        "total_tasks": 30,
        "completed_tasks": 15,
        "pending_tasks": 15,
        "avg_workload": 35.0,
        "estimated_hours": 450.0,
        "actual_hours": 220.0,
        "deadline_days_remaining": 25,
        "previous_delays": 1,
        "budget": 900000.0,
        "spent_budget": 450000.0,
        "task_complexity": 2.0,
        "dependencies": 3
    })
    assert "delay_probability" in pred
    assert "risk_score" in pred
    assert "risk_level" in pred
    assert "expected_delay_days" in pred


def test_predict_risk_with_project_id_persistence():
    """Test 7: Verify project_id persistence and 404 validation."""
    # Find existing project
    p_res = client.get("/api/projects")
    projects = p_res.json()
    assert len(projects) > 0
    valid_proj_id = projects[0]["id"]

    payload = {
        "team_size": 4,
        "total_tasks": 20,
        "completed_tasks": 16,
        "pending_tasks": 4,
        "avg_workload": 30.0,
        "estimated_hours": 300.0,
        "actual_hours": 210.0,
        "deadline_days_remaining": 30,
        "previous_delays": 0,
        "budget": 600000.0,
        "spent_budget": 420000.0,
        "task_complexity": 1.0,
        "dependencies": 1,
        "project_id": valid_proj_id
    }

    # Request with valid project_id
    res = client.post("/api/predict-risk", json=payload)
    assert res.status_code == 200
    assert res.json()["project_id"] == valid_proj_id

    # Verify prediction persisted in DB
    db = SessionLocal()
    persisted = db.query(models.Prediction).filter(models.Prediction.project_id == valid_proj_id).all()
    assert len(persisted) >= 1
    db.close()

    # Request with non-existent project_id
    bad_payload = payload.copy()
    bad_payload["project_id"] = 999999
    bad_res = client.post("/api/predict-risk", json=bad_payload)
    assert bad_res.status_code == 404


def test_password_strength_validation():
    """Verify strong password policy: min 8 chars, letter, and number."""
    base_email = f"pwd.test.{models.datetime.utcnow().timestamp()}@example.com"

    # Too short (< 8 chars)
    res_short = client.post("/api/auth/register", json={
        "name": "Short Pwd",
        "email": f"short.{base_email}",
        "password": "abc1",
        "role": "ROLE_MEMBER"
    })
    assert res_short.status_code == 422

    # Letters only (no number)
    res_no_num = client.post("/api/auth/register", json={
        "name": "No Num",
        "email": f"nonum.{base_email}",
        "password": "passwordonly",
        "role": "ROLE_MEMBER"
    })
    assert res_no_num.status_code == 422

    # Numbers only (no letter)
    res_no_let = client.post("/api/auth/register", json={
        "name": "No Let",
        "email": f"nolet.{base_email}",
        "password": "1234567890",
        "role": "ROLE_MEMBER"
    })
    assert res_no_let.status_code == 422

    # Valid alphanumeric 8+
    res_valid = client.post("/api/auth/register", json={
        "name": "Valid Pwd",
        "email": f"valid.{base_email}",
        "password": "SecurePassword2026",
        "role": "ROLE_MEMBER"
    })
    assert res_valid.status_code == 201


def test_forgot_password_and_verification_code_flow():
    """Verify OTP verification code lifecycle: generation, expiry, attempts, and single-use."""
    user_email = f"reset.user.{models.datetime.utcnow().timestamp()}@example.com"
    client.post("/api/auth/register", json={
        "name": "Reset Candidate",
        "email": user_email,
        "password": "InitialPassword123",
        "role": "ROLE_PM"
    })

    # Invalid email format
    bad_email_res = client.post("/api/auth/forgot-password", json={"email": "not-an-email"})
    assert bad_email_res.status_code == 422

    # Non-existent email -> 200 (prevent enumeration)
    ghost_res = client.post("/api/auth/forgot-password", json={"email": "nonexistent@nowhere.com"})
    assert ghost_res.status_code == 200
    assert "If an account exists" in ghost_res.json()["message"]

    # Valid request
    forgot_res = client.post("/api/auth/forgot-password", json={"email": user_email})
    assert forgot_res.status_code == 200
    assert "If an account exists" in forgot_res.json()["message"]

    # Retrieve active code directly from DB
    from app import crud
    db = SessionLocal()
    code_rec = crud.get_latest_reset_code(db, user_email)
    assert code_rec is not None
    assert code_rec.is_used is False
    assert code_rec.attempts == 0

    # Wrong code attempt
    wrong_res = client.post("/api/auth/verify-reset-code", json={
        "email": user_email,
        "code": "000000"
    })
    assert wrong_res.status_code == 400
    assert "invalid" in wrong_res.json()["detail"].lower()

    # Verify attempt incremented in DB
    db.refresh(code_rec)
    assert code_rec.attempts == 1

    # Simulate attempt limit exceeded
    code_rec.attempts = 5
    db.commit()
    max_res = client.post("/api/auth/verify-reset-code", json={
        "email": user_email,
        "code": "000000"
    })
    assert max_res.status_code == 400
    assert "too many" in max_res.json()["detail"].lower()

    # Re-issue new code
    forgot_res2 = client.post("/api/auth/forgot-password", json={"email": user_email})
    assert forgot_res2.status_code == 200
    new_code_rec = crud.get_latest_reset_code(db, user_email)
    assert new_code_rec.id != code_rec.id

    # Simulate expired code
    from datetime import datetime, timedelta
    new_code_rec.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    expired_res = client.post("/api/auth/verify-reset-code", json={
        "email": user_email,
        "code": "111111"
    })
    assert expired_res.status_code == 400
    assert "expired" in expired_res.json()["detail"].lower()

    # Re-issue valid code for successful verification
    crud.create_password_reset_code(db, user_email, "654321", expires_in_minutes=10)
    db.close()

    success_verify = client.post("/api/auth/verify-reset-code", json={
        "email": user_email,
        "code": "654321"
    })
    assert success_verify.status_code == 200
    verify_data = success_verify.json()
    assert "reset_token" in verify_data
    token = verify_data["reset_token"]

    # Reusing verified code must fail
    reuse_code = client.post("/api/auth/verify-reset-code", json={
        "email": user_email,
        "code": "654321"
    })
    assert reuse_code.status_code == 400


def test_password_reset_and_login_flow():
    """Verify reset token security: password update, single-use, old vs new password login."""
    user_email = f"full.reset.{models.datetime.utcnow().timestamp()}@example.com"
    old_password = "OldPassword1"
    new_password = "NewPassword2026"

    # Register user
    client.post("/api/auth/register", json={
        "name": "Password Reset User",
        "email": user_email,
        "password": old_password,
        "role": "ROLE_MEMBER"
    })

    # Trigger forgot password and obtain valid reset token
    client.post("/api/auth/forgot-password", json={"email": user_email})
    from app import crud
    db = SessionLocal()
    crud.create_password_reset_code(db, user_email, "987654", expires_in_minutes=10)
    db.close()

    verify_res = client.post("/api/auth/verify-reset-code", json={
        "email": user_email,
        "code": "987654"
    })
    assert verify_res.status_code == 200
    reset_token = verify_res.json()["reset_token"]

    # Weak password attempt on reset
    weak_reset = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "weak"
    })
    assert weak_reset.status_code == 422

    # Invalid token attempt
    bad_token_res = client.post("/api/auth/reset-password", json={
        "reset_token": "invalid_token_12345",
        "new_password": new_password
    })
    assert bad_token_res.status_code == 400

    # Successful password reset
    good_reset = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": new_password
    })
    assert good_reset.status_code == 200
    assert "Password updated successfully" in good_reset.json()["message"]

    # Reusing token must fail (single-use)
    reuse_token_res = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "AnotherPassword9"
    })
    assert reuse_token_res.status_code == 400

    # Login with OLD password must fail
    old_login = client.post("/api/auth/login", json={
        "email": user_email,
        "password": old_password
    })
    assert old_login.status_code == 401

    # Login with NEW password must succeed
    new_login = client.post("/api/auth/login", json={
        "email": user_email,
        "password": new_password
    })
    assert new_login.status_code == 200
    assert new_login.json()["email"] == user_email


def test_email_verification_invalid_and_expired_tokens():
    """Test validation of missing, invalid, expired, and single-use verification tokens."""
    # 1. Missing token
    res_missing = client.get("/api/auth/verify-email?token=")
    assert res_missing.status_code == 400
    assert "Verification token is required" in res_missing.json()["detail"]

    # 2. Invalid token
    res_invalid = client.get("/api/auth/verify-email?token=invalid_nonexistent_token_123")
    assert res_invalid.status_code == 400
    assert "invalid" in res_invalid.json()["detail"].lower()

    # 3. Expired token
    expired_email = f"expired.user.{datetime.utcnow().timestamp()}@example.com"
    client.post("/api/auth/register", json={
        "name": "Expired Tester",
        "email": expired_email,
        "password": "Password123",
        "role": "ROLE_MEMBER"
    })

    db = SessionLocal()
    user = crud.get_user_by_email(db, expired_email)
    raw_token = crud.issue_email_verification_token(db, user)
    # Manually expire token
    user.email_verification_expires_at = datetime.utcnow() - timedelta(hours=1)
    db.commit()
    db.close()

    res_expired = client.get(f"/api/auth/verify-email?token={raw_token}")
    assert res_expired.status_code == 400
    assert "expired" in res_expired.json()["detail"].lower()

    # 4. Valid token verification and single-use invalidation
    valid_email = f"valid.singleuse.{datetime.utcnow().timestamp()}@example.com"
    client.post("/api/auth/register", json={
        "name": "Single Use",
        "email": valid_email,
        "password": "Password123",
        "role": "ROLE_PM"
    })

    db = SessionLocal()
    valid_user = crud.get_user_by_email(db, valid_email)
    valid_token = crud.issue_email_verification_token(db, valid_user)
    db.close()

    res_success = client.get(f"/api/auth/verify-email?token={valid_token}")
    assert res_success.status_code == 200
    assert "Email verified successfully" in res_success.json()["message"]

    # Attempt to reuse consumed token must fail
    res_reuse = client.get(f"/api/auth/verify-email?token={valid_token}")
    assert res_reuse.status_code == 400
    assert "invalid" in res_reuse.json()["detail"].lower()


def test_resend_email_verification_and_cooldown():
    """Test resending verification link, cooldown rate limiting, and enumeration resistance."""
    # 1. Non-existent email returns neutral success response (enumeration resistant)
    res_unknown = client.post("/api/auth/resend-verification", json={"email": "nobody.exists@example.com"})
    assert res_unknown.status_code == 200
    assert "If an account exists" in res_unknown.json()["message"]

    # 2. Existing unverified account
    resend_email = f"resend.tester.{datetime.utcnow().timestamp()}@example.com"
    client.post("/api/auth/register", json={
        "name": "Resend Tester",
        "email": resend_email,
        "password": "Password123",
        "role": "ROLE_PM"
    })

    # Rapid second resend within 60s cooldown must trigger 429
    res_cooldown = client.post("/api/auth/resend-verification", json={"email": resend_email})
    assert res_cooldown.status_code == 429
    assert "60 seconds" in res_cooldown.json()["detail"]

    # Fast-forward cooldown window in DB
    db = SessionLocal()
    user = crud.get_user_by_email(db, resend_email)
    user.email_verification_expires_at = datetime.utcnow() + timedelta(hours=23, minutes=58)
    db.commit()
    db.close()

    # Resend after cooldown succeeds
    res_allowed = client.post("/api/auth/resend-verification", json={"email": resend_email})
    assert res_allowed.status_code == 200
    assert "verification link has been sent" in res_allowed.json()["message"]

    # 3. Already verified account indicates already verified
    db = SessionLocal()
    user = crud.get_user_by_email(db, resend_email)
    user.email_verified = True
    db.commit()
    db.close()

    res_already = client.post("/api/auth/resend-verification", json={"email": resend_email})
    assert res_already.status_code == 200
    assert res_already.json()["already_verified"] is True



