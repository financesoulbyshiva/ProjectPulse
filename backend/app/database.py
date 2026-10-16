import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./projectpulse.db")

# Ensure default SQLite path resolves consistently to backend/projectpulse.db regardless of CWD
if DATABASE_URL == "sqlite:///./projectpulse.db":
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(backend_dir, "projectpulse.db")
    DATABASE_URL = f"sqlite:///{db_file}"

# For SQLite, check_same_thread needs to be False for FastAPI multi-threaded requests
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that yields an active database session and closes it on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """Safely apply non-destructive schema migrations for SQLite."""
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            if columns:  # table exists
                if "job_title" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN job_title VARCHAR(100)"))
                    conn.commit()

                if "role" in columns:
                    conn.execute(text("""
                        UPDATE users
                        SET job_title = CASE
                                WHEN role IN ('ROLE_ADMIN', 'ROLE_ANALYST') THEN role
                                WHEN role = 'ROLE_PM' THEN COALESCE(job_title, 'Project Manager')
                                WHEN role = 'ROLE_MEMBER' THEN COALESCE(job_title, 'Team Member')
                                ELSE COALESCE(job_title, role)
                            END,
                            role = CASE
                                WHEN role IN ('ROLE_ADMIN', 'ROLE_PM', 'ROLE_MEMBER', 'ROLE_ANALYST') THEN role
                                WHEN upper(role) = 'ADMIN' THEN 'ROLE_ADMIN'
                                WHEN upper(role) IN ('PROJECT MANAGER', 'PM') THEN 'ROLE_PM'
                                WHEN upper(role) IN ('TEAM MEMBER', 'MEMBER', 'ENGINEER') THEN 'ROLE_MEMBER'
                                WHEN upper(role) IN ('DATA ANALYST', 'ANALYST') THEN 'ROLE_ANALYST'
                                ELSE 'ROLE_MEMBER'
                            END
                    """))
                    conn.commit()

                if "email_verified" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0"))
                    conn.execute(text("UPDATE users SET email_verified = 1"))
                    conn.commit()
                if "email_verification_token_hash" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_token_hash VARCHAR(128)"))
                    conn.commit()
                if "email_verification_expires_at" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_expires_at DATETIME"))
                    conn.commit()
        except Exception as e:
            print(f"[DB MIGRATION NOTICE] {e}")


def init_db():
    """Create all registered database tables and apply non-destructive migrations."""
    Base.metadata.create_all(bind=engine)
    migrate_db()
