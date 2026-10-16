"""
ProjectPulse — Local Development Demo User Seeder
Safely provisions an idempotent demo account for local demonstrations.
Refuses execution if ENVIRONMENT is set to 'production' or 'prod'.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in sys.path regardless of execution working directory
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure root directory is in sys.path if nested
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Preserve process-level ENVIRONMENT if explicitly set in shell/container
process_env = os.environ.get("ENVIRONMENT")
load_dotenv(backend_dir / ".env")
load_dotenv(root_dir / ".env")
if process_env:
    os.environ["ENVIRONMENT"] = process_env


DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo.projectpulse@example.com")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")
DEMO_NAME = os.getenv("DEMO_NAME", "Demo Project Manager")
DEMO_ROLE = os.getenv("DEMO_ROLE", "ROLE_PM")
DEMO_JOB_TITLE = os.getenv("DEMO_JOB_TITLE", "Lead Project Manager (Demo)")


def enforce_security_boundary():
    """Refuse to seed demo accounts in production environments."""
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    if env in ("production", "prod", "live"):
        print(f"[SECURITY ALERT] Refusing to seed demo account in production environment (ENVIRONMENT='{env}').")
        sys.exit(1)


def seed_demo_user():
    """Idempotently seed the verified demo account."""
    enforce_security_boundary()

    if not DEMO_PASSWORD:
        print("[SECURITY CHECK] DEMO_PASSWORD environment variable is not set.")
        print("Please configure DEMO_PASSWORD in your local environment or .env file before running.")
        sys.exit(1)

    from app.database import SessionLocal, init_db
    from app import models, crud

    init_db()
    db = SessionLocal()

    try:
        user = crud.get_user_by_email(db, DEMO_EMAIL)

        if user:
            # Check if password already matches and user is verified
            pwd_matches = crud.verify_password(DEMO_PASSWORD, user.password_hash)
            needs_update = False

            if not user.email_verified:
                user.email_verified = True
                user.email_verification_token_hash = None
                user.email_verification_expires_at = None
                needs_update = True
                print(f"[INFO] Demo account '{DEMO_EMAIL}' updated: marked email_verified=True.")

            if not pwd_matches:
                # Update password if explicitly different to match demo specification
                user.password_hash = crud.hash_password(DEMO_PASSWORD)
                needs_update = True
                print(f"[INFO] Demo account '{DEMO_EMAIL}' password synchronized.")

            if needs_update:
                db.commit()
                db.refresh(user)
            else:
                print(f"[INFO] Demo account '{DEMO_EMAIL}' already exists, is verified, and is ready for use.")

            return user

        # Create new verified demo account
        hashed_password = crud.hash_password(DEMO_PASSWORD)
        demo_user = models.User(
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=hashed_password,
            role=DEMO_ROLE,
            job_title=DEMO_JOB_TITLE,
            email_verified=True,
            email_verification_token_hash=None,
            email_verification_expires_at=None,
            created_at=datetime.utcnow()
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print(f"[SUCCESS] Demo user '{DEMO_EMAIL}' created successfully with verified status.")
        return demo_user

    finally:
        db.close()


if __name__ == "__main__":
    print("==================================================")
    print("      PROJECTPULSE — LOCAL DEMO ACCOUNT SEEDER     ")
    print("==================================================")
    seed_demo_user()
