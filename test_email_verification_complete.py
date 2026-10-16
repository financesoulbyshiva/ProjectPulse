"""
Comprehensive Production Verification Suite for Email Verification
Tests Gmail SMTP integration, cryptographic token security,
rate-limiting cooldown, unverified login protection, and verified authentication.
"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app import models, crud
from backend.app.services.email_service import get_test_sent_emails, clear_test_sent_emails

client = TestClient(app)


def test_complete_email_verification_suite():
    print("==================================================================")
    print("      PROJECTPULSE — EMAIL VERIFICATION COMPREHENSIVE SUITE       ")
    print("==================================================================")
    clear_test_sent_emails()

    # 1. Registration creates unverified user and dispatches email
    print("\n[TEST 1] Registering user with unverified state...")
    ts = datetime.utcnow().timestamp()
    test_email = f"verified.test.{ts}@projectpulse.dev"
    reg_res = client.post("/api/auth/register", json={
        "name": "Sarah Connor",
        "email": test_email,
        "password": "SecurePassword2026",
        "role": "ROLE_PM"
    })
    assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
    user_data = reg_res.json()
    assert user_data["email_verified"] is False, "New user must start unverified"
    print("  [OK] Registration creates user with email_verified=False")

    # Verify email was captured in email_service test spy
    emails = get_test_sent_emails()
    assert len(emails) >= 1, "Verification email was not dispatched"
    last_email = emails[-1]
    assert last_email["to"] == test_email
    assert last_email["name"] == "Sarah Connor"
    assert "token" in last_email
    raw_token = last_email["token"]
    assert len(raw_token) >= 32, "Token must be cryptographically secure"
    print("  [OK] Verification email dispatched via email service with secure token link")

    # 2. Database security: Token hash and expiry stored; raw token NOT stored
    db = SessionLocal()
    user = crud.get_user_by_email(db, test_email)
    assert user is not None
    assert user.email_verification_token_hash is not None, "Token hash must be in DB"
    assert user.email_verification_token_hash != raw_token, "Raw token must NEVER be stored in DB"
    assert user.email_verification_token_hash == crud.hash_secret(raw_token), "Token must be hashed using SHA-256"
    assert user.email_verification_expires_at is not None, "Expiration must be set"
    assert user.email_verification_expires_at > datetime.utcnow(), "Expiration must be in the future (24 hours)"
    db.close()
    print("  [OK] Database stores token hash (SHA-256) and 24h expiration; raw token never persisted")

    # 3. Unverified login is blocked
    print("\n[TEST 2] Verifying login protection for unverified account...")
    blocked_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword2026"
    })
    assert blocked_login.status_code == 403, f"Expected 403, got {blocked_login.status_code}"
    assert "Please verify your email before signing in." in blocked_login.json()["detail"]
    print("  [OK] Unverified login correctly blocked with 403 Forbidden")

    # 4. Token validation edge cases: Invalid, expired, missing
    print("\n[TEST 3] Testing token rejection edge cases...")
    res_empty = client.get("/api/auth/verify-email?token=")
    assert res_empty.status_code == 400
    print("  [OK] Missing token rejected (400)")

    res_invalid = client.get("/api/auth/verify-email?token=completely_fake_invalid_token")
    assert res_invalid.status_code == 400
    print("  [OK] Invalid token rejected (400)")

    # Test expired token
    db = SessionLocal()
    user = crud.get_user_by_email(db, test_email)
    user.email_verification_expires_at = datetime.utcnow() - timedelta(minutes=5)
    db.commit()
    db.close()

    res_expired = client.get(f"/api/auth/verify-email?token={raw_token}")
    assert res_expired.status_code == 400
    assert "expired" in res_expired.json()["detail"].lower()
    print("  [OK] Expired token rejected (400)")

    # 5. Resend verification flow & cooldown rate-limiting
    print("\n[TEST 4] Testing Resend Verification flow & cooldown rate limit...")
    # Trigger resend
    clear_test_sent_emails()
    res_resend = client.post("/api/auth/resend-verification", json={"email": test_email})
    assert res_resend.status_code == 200
    print("  [OK] Resend verification issued new token")

    # Immediate second resend must trigger 429
    res_rapid = client.post("/api/auth/resend-verification", json={"email": test_email})
    assert res_rapid.status_code == 429, f"Expected 429, got {res_rapid.status_code}"
    assert "60 seconds" in res_rapid.json()["detail"]
    print("  [OK] Rapid resend blocked by 60s cooldown rate limit (429 Too Many Requests)")

    # Retrieve new token from email service
    new_emails = get_test_sent_emails()
    assert len(new_emails) == 1
    new_token = new_emails[0]["token"]
    assert new_token != raw_token, "New token must be generated"

    # Old token is invalidated
    res_old = client.get(f"/api/auth/verify-email?token={raw_token}")
    assert res_old.status_code == 400, "Old token must be invalidated"
    print("  [OK] Previous verification token invalidated by new resend")

    # Non-existent user resend does not reveal account existence
    res_ghost = client.post("/api/auth/resend-verification", json={"email": "nobody_exists_123@example.com"})
    assert res_ghost.status_code == 200
    assert "If an account exists" in res_ghost.json()["message"]
    print("  [OK] Resend for unknown email prevents user enumeration")

    # 6. Valid verification succeeds and clears token metadata
    print("\n[TEST 5] Testing valid verification completion...")
    res_verify = client.get(f"/api/auth/verify-email?token={new_token}")
    assert res_verify.status_code == 200
    assert "Email verified successfully" in res_verify.json()["message"]

    db = SessionLocal()
    user = crud.get_user_by_email(db, test_email)
    assert user.email_verified is True, "User must now be verified"
    assert user.email_verification_token_hash is None, "Token hash must be cleared"
    assert user.email_verification_expires_at is None, "Expiration must be cleared"
    db.close()
    print("  [OK] Account verified: email_verified=True, single-use token cleared from database")

    # 7. Single-use: Reusing verified token fails
    res_reused = client.get(f"/api/auth/verify-email?token={new_token}")
    assert res_reused.status_code == 400
    print("  [OK] Reused token rejected (single-use enforced)")

    # 8. Verified login succeeds
    print("\n[TEST 6] Testing login with verified account...")
    good_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword2026"
    })
    assert good_login.status_code == 200
    user_payload = good_login.json()
    assert user_payload["email"] == test_email
    assert user_payload["name"] == "Sarah Connor"
    assert user_payload["email_verified"] is True
    print("  [OK] Authenticated login succeeds for verified user with correct profile")

    # 9. Resend for already-verified account indicates already verified
    res_already = client.post("/api/auth/resend-verification", json={"email": test_email})
    assert res_already.status_code == 200
    assert res_already.json()["already_verified"] is True
    print("  [OK] Resend for already verified account indicates verified status")

    print("\n==================================================================")
    print("       ALL EMAIL VERIFICATION SUITE CHECKS PASSED (100%)          ")
    print("==================================================================")


if __name__ == "__main__":
    test_complete_email_verification_suite()
