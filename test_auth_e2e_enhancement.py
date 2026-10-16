import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app import models, crud

client = TestClient(app)

print("==================================================")
print("  STEP 24: POSITIVE AUTHENTICATION E2E TEST")
print("==================================================")

email = f"e2e.tester.{datetime.utcnow().timestamp()}@projectpulse.dev"
original_pwd = "OriginalPassword123"
new_pwd = "NewSecurePassword2026"

# 1. Register
print("\n[1] Registering user:", email)
reg_res = client.post("/api/auth/register", json={
    "name": "E2E Tester",
    "email": email,
    "password": original_pwd,
    "role": "ROLE_PM"
})
assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
print(" -> Registration SUCCESS")

# 2. Verify unverified login is blocked
print("\n[2] Attempting login before email verification (must be blocked)...")
unverified_res = client.post("/api/auth/login", json={
    "email": email,
    "password": original_pwd
})
assert unverified_res.status_code == 403, f"Expected 403, got {unverified_res.status_code}"
print(" -> Unverified login correctly rejected (403)")

# Verify email via token
print("\n[2b] Verifying email address with verification token...")
db = SessionLocal()
u = crud.get_user_by_email(db, email)
token = crud.issue_email_verification_token(db, u)
db.close()
verify_email_res = client.get(f"/api/auth/verify-email?token={token}")
assert verify_email_res.status_code == 200
print(" -> Email verification SUCCESS")

# Login with original credentials
print("\n[2c] Logging in with original password after verification...")
login_res = client.post("/api/auth/login", json={
    "email": email,
    "password": original_pwd
})
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
print(" -> Login SUCCESS:", login_res.json()["name"])

# 3. Forgot Password request
print("\n[3] Initiating Forgot Password for:", email)
forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
assert forgot_res.status_code == 200
print(" -> Forgot Password response:", forgot_res.json()["message"])

# 4. Fetch the generated OTP code from database
db = SessionLocal()
active_code_rec = crud.get_latest_reset_code(db, email)
assert active_code_rec is not None
db.close()
# Also verify dev_code in response
otp_code = forgot_res.json().get("dev_code")
print(f" -> Received 6-digit OTP Code: {otp_code}")
assert otp_code is not None and len(otp_code) == 6

# 5. Verify reset code
print("\n[5] Verifying OTP code...")
verify_res = client.post("/api/auth/verify-reset-code", json={
    "email": email,
    "code": otp_code
})
assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"
reset_token = verify_res.json()["reset_token"]
print(" -> Verification SUCCESS. Received reset_token:", reset_token[:12] + "...")

# 6. Reset password
print("\n[6] Resetting password to:", new_pwd)
reset_res = client.post("/api/auth/reset-password", json={
    "reset_token": reset_token,
    "new_password": new_pwd
})
assert reset_res.status_code == 200, f"Reset failed: {reset_res.text}"
print(" -> Reset Password SUCCESS:", reset_res.json()["message"])

# 7. Old password must NO LONGER work
print("\n[7] Verifying old password is invalidated...")
old_login = client.post("/api/auth/login", json={
    "email": email,
    "password": original_pwd
})
assert old_login.status_code == 401, "Old password should not work!"
print(" -> Old password correctly rejected (401)")

# 8. New password MUST work
print("\n[8] Logging in with new password...")
new_login = client.post("/api/auth/login", json={
    "email": email,
    "password": new_pwd
})
assert new_login.status_code == 200, f"New login failed: {new_login.text}"
print(" -> Login with new password SUCCESS!")

print("\n==================================================")
print("  STEP 25: NEGATIVE AUTHENTICATION TESTS")
print("==================================================")

# 1. Wrong OTP code
print("\n[Neg 1] Testing wrong OTP code...")
client.post("/api/auth/forgot-password", json={"email": email})
wrong_code_res = client.post("/api/auth/verify-reset-code", json={
    "email": email,
    "code": "999999"
})
assert wrong_code_res.status_code == 400
assert "invalid" in wrong_code_res.json()["detail"].lower()
print(" -> Wrong code correctly rejected (400)")

# 2. Expired OTP code
print("\n[Neg 2] Testing expired OTP code...")
db = SessionLocal()
code_rec = crud.get_latest_reset_code(db, email)
code_rec.expires_at = datetime.utcnow() - timedelta(minutes=5)
db.commit()
db.close()
expired_code_res = client.post("/api/auth/verify-reset-code", json={
    "email": email,
    "code": "123456"
})
assert expired_code_res.status_code == 400
assert "expired" in expired_code_res.json()["detail"].lower()
print(" -> Expired code correctly rejected (400)")

# 3. Weak password on reset
print("\n[Neg 3] Testing weak password on reset...")
# Generate fresh token
db = SessionLocal()
crud.create_password_reset_code(db, email, "777888", expires_in_minutes=10)
db.close()
v_res = client.post("/api/auth/verify-reset-code", json={"email": email, "code": "777888"})
fresh_token = v_res.json()["reset_token"]

weak_res = client.post("/api/auth/reset-password", json={
    "reset_token": fresh_token,
    "new_password": "short"
})
assert weak_res.status_code == 422
print(" -> Weak password rejected by Pydantic (422)")

# 4. Token reuse
print("\n[Neg 4] Testing token reuse after successful reset...")
ok_reset = client.post("/api/auth/reset-password", json={
    "reset_token": fresh_token,
    "new_password": "ValidPassword999"
})
assert ok_reset.status_code == 200

reuse_res = client.post("/api/auth/reset-password", json={
    "reset_token": fresh_token,
    "new_password": "ValidPassword999"
})
assert reuse_res.status_code == 400
assert "already used" in reuse_res.json()["detail"].lower()
print(" -> Reused reset token correctly rejected (400)")

# 5. Invalid email format
print("\n[Neg 5] Testing invalid email format...")
bad_email = client.post("/api/auth/forgot-password", json={"email": "not-valid"})
assert bad_email.status_code == 422
print(" -> Invalid email format correctly rejected (422)")

# 6. Password with only letters (no number)
print("\n[Neg 6] Testing password without numbers...")
no_num = client.post("/api/auth/register", json={
    "name": "Test",
    "email": "test@example.com",
    "password": "onlylettershere",
    "role": "ROLE_PM"
})
assert no_num.status_code == 422
print(" -> Letter-only password correctly rejected (422)")

# 7. Password with only numbers (no letters)
print("\n[Neg 7] Testing password without letters...")
no_let = client.post("/api/auth/register", json={
    "name": "Test",
    "email": "test@example.com",
    "password": "1234567890",
    "role": "ROLE_PM"
})
assert no_let.status_code == 422
print(" -> Number-only password correctly rejected (422)")

print("\nALL POSITIVE AND NEGATIVE E2E AUTHENTICATION TESTS PASSED!")
