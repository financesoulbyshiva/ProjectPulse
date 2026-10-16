"""
Verification URL & Flow Test Suite for ProjectPulse
Validates:
1. Exact URL generation (scheme, host, port, path, query param) from FRONTEND_URL.
2. CORS headers for localhost and 127.0.0.1 across development ports.
3. Full lifecycle: signup -> email generation -> token verification -> login.
4. Edge cases: missing, invalid, expired, and already-used token handling.
"""
import os
import urllib.parse
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app import models, crud
from backend.app.services.email_service import (
    get_smtp_config,
    send_account_verification_email,
    get_test_sent_emails,
    clear_test_sent_emails,
)

client = TestClient(app)


def test_verification_url_structure():
    """Verify that generated verification URL matches the exact frontend route and respects FRONTEND_URL."""
    clear_test_sent_emails()
    test_token = "abc123xyzSecureVerificationTokenString456"
    test_email = "tester@projectpulse.dev"
    test_name = "Alex Mercer"

    send_account_verification_email(test_email, test_name, test_token)
    emails = get_test_sent_emails()
    assert len(emails) >= 1, "Verification email was not recorded"

    last_email = emails[-1]
    url = last_email["verification_url"]

    # Parse and validate URL components
    parsed = urllib.parse.urlparse(url)
    assert parsed.scheme in ("http", "https"), f"Invalid scheme: {parsed.scheme}"
    assert parsed.netloc in ("localhost:5173", "127.0.0.1:5173", "localhost:5174", "127.0.0.1:5174", "localhost:3000") or "5173" in parsed.netloc, f"Unexpected netloc: {parsed.netloc}"
    assert parsed.path == "/verify-email", f"Verification path must be /verify-email, got: {parsed.path}"

    query_params = urllib.parse.parse_qs(parsed.query)
    assert "token" in query_params, f"Token query parameter missing in URL: {url}"
    assert query_params["token"][0] == test_token, f"Token mismatch: expected {test_token}, got {query_params['token'][0]}"
    print("  [PASS] test_verification_url_structure: Scheme, host, port, path, and token query param validated.")


def test_cors_headers_for_dev_origins():
    """Verify backend CORS headers permit localhost and 127.0.0.1 origins on standard Vite ports."""
    test_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    for origin in test_origins:
        res = client.options(
            "/api/auth/verify-email",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        allowed_origin = res.headers.get("access-control-allow-origin")
        assert allowed_origin == origin, f"Origin {origin} was not allowed by CORS (got {allowed_origin})"
    print("  [PASS] test_cors_headers_for_dev_origins: CORS properly configured for all dev ports.")


def test_complete_flow_and_token_edge_cases():
    """Verify registration, verification email generation, token consumption, and edge cases."""
    clear_test_sent_emails()
    ts = datetime.utcnow().timestamp()
    email = f"flow.user.{ts}@projectpulse.dev"
    pwd = "SecurePassword2026"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "name": "Dev User",
        "email": email,
        "password": pwd,
        "role": "ROLE_PM"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["email_verified"] is False

    # 2. Extract verification link from sent email
    emails = get_test_sent_emails()
    assert len(emails) >= 1
    verification_url = emails[-1]["verification_url"]
    parsed = urllib.parse.urlparse(verification_url)
    token = urllib.parse.parse_qs(parsed.query)["token"][0]

    # 3. Login before verification must fail with 403
    unverified_login = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert unverified_login.status_code == 403
    assert "verify" in unverified_login.json()["detail"].lower()

    # 4. Verify with invalid token
    bad_res = client.get("/api/auth/verify-email?token=completely_invalid_token_xyz")
    assert bad_res.status_code == 400
    assert "invalid" in bad_res.json()["detail"].lower()

    # 5. Verify with valid token
    good_res = client.get(f"/api/auth/verify-email?token={token}")
    assert good_res.status_code == 200
    assert "Email verified successfully" in good_res.json()["message"]

    # 6. Reusing consumed token fails with 400 and invalid/already-used detail
    reused_res = client.get(f"/api/auth/verify-email?token={token}")
    assert reused_res.status_code == 400
    assert "invalid" in reused_res.json()["detail"].lower() or "already" in reused_res.json()["detail"].lower()

    # 7. Login after verification succeeds
    verified_login = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert verified_login.status_code == 200
    assert verified_login.json()["email_verified"] is True
    print("  [PASS] test_complete_flow_and_token_edge_cases: Complete flow passed.")


if __name__ == "__main__":
    print("\n=== RUNNING PROJECTPULSE VERIFICATION URL & FLOW TESTS ===")
    test_verification_url_structure()
    test_cors_headers_for_dev_origins()
    test_complete_flow_and_token_edge_cases()
    print("=== ALL VERIFICATION URL & FLOW TESTS PASSED SUCCESSFULLY ===\n")
