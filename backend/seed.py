"""
ProjectPulse Database Seeder
Populates initial realistic demo data for Users, Projects, Tasks, and Team allocations.
"""
from datetime import datetime, date, timedelta
from app.database import SessionLocal, init_db
from app import models, crud


def seed():
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(models.User).count() > 0:
            print("[INFO] Database already contains records. Skipping seed.")
            return

        print("[INFO] Seeding ProjectPulse database with realistic data...")

        # 1. Create Users
        users_data = [
            {"name": "Rahul Sharma", "email": "rahul.sharma@projectpulse.dev", "role": "ROLE_PM"},
            {"name": "Sneha Patil", "email": "sneha.patil@projectpulse.dev", "role": "ROLE_MEMBER"},
            {"name": "Amit Verma", "email": "amit.verma@projectpulse.dev", "role": "ROLE_MEMBER"},
            {"name": "Priya Deshmukh", "email": "priya.deshmukh@projectpulse.dev", "role": "ROLE_MEMBER"},
        ]

        created_users = {}
        for u in users_data:
            hashed_pwd = crud.hash_password("password123")
            db_user = models.User(
                name=u["name"],
                email=u["email"],
                password_hash=hashed_pwd,
                role=u["role"],
                email_verified=True,
                created_at=datetime.utcnow()
            )
            db.add(db_user)
            db.flush()
            created_users[u["name"]] = db_user

        rahul = created_users["Rahul Sharma"]
        sneha = created_users["Sneha Patil"]
        amit = created_users["Amit Verma"]
        priya = created_users["Priya Deshmukh"]

        # 2. Create Projects
        today = date.today()

        p1 = models.Project(
            name="Mobile Application",
            description="Cross-platform student mobile client for attendance, grade access, and notification sync.",
            start_date=(today - timedelta(days=45)).strftime("%Y-%m-%d"),
            deadline=(today + timedelta(days=12)).strftime("%Y-%m-%d"),  # Approaching deadline
            budget=120000.0,
            actual_cost=98000.0,
            status="AT_RISK",
            complexity="HIGH",
            dependencies=4,
            manager_id=rahul.id,
            team_members=[rahul, sneha, amit, priya],
            created_at=datetime.utcnow()
        )

        p2 = models.Project(
            name="College Management Portal",
            description="Administrative web portal for student admissions, fee reconciliation, and faculty duty rosters.",
            start_date=(today - timedelta(days=60)).strftime("%Y-%m-%d"),
            deadline=(today + timedelta(days=35)).strftime("%Y-%m-%d"),
            budget=80000.0,
            actual_cost=62000.0,
            status="ON_TRACK",
            complexity="MEDIUM",
            dependencies=2,
            manager_id=sneha.id,
            team_members=[sneha, amit, priya],
            created_at=datetime.utcnow()
        )

        p3 = models.Project(
            name="AI Analytics Platform",
            description="Predictive institutional analytics dashboard aggregating student performance trends.",
            start_date=(today - timedelta(days=20)).strftime("%Y-%m-%d"),
            deadline=(today + timedelta(days=65)).strftime("%Y-%m-%d"),
            budget=95000.0,
            actual_cost=34000.0,
            status="ON_TRACK",
            complexity="HIGH",
            dependencies=3,
            manager_id=amit.id,
            team_members=[amit, rahul, priya],
            created_at=datetime.utcnow()
        )

        p4 = models.Project(
            name="Website Redesign",
            description="Modernization of public university portal with accessible navigation and responsive templates.",
            start_date=(today - timedelta(days=50)).strftime("%Y-%m-%d"),
            deadline=(today - timedelta(days=3)).strftime("%Y-%m-%d"),  # Past deadline with pending tasks -> DELAYED
            budget=45000.0,
            actual_cost=48000.0,
            status="DELAYED",
            complexity="MEDIUM",
            dependencies=3,
            manager_id=priya.id,
            team_members=[priya, sneha, rahul],
            created_at=datetime.utcnow()
        )

        db.add_all([p1, p2, p3, p4])
        db.flush()

        # 3. Create Tasks
        tasks_data = [
            # Mobile Application (p1)
            {
                "project_id": p1.id,
                "title": "Implement Push Notification Handler",
                "description": "Configure FCM and APNS background workers with client token management.",
                "assigned_to": amit.id,
                "priority": "HIGH",
                "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "status": "IN_PROGRESS",
                "estimated_hours": 20.0,
                "actual_hours": 16.0
            },
            {
                "project_id": p1.id,
                "title": "Offline SQLite Data Synchronization",
                "description": "Build local dirty state conflict resolution and client schema migration.",
                "assigned_to": rahul.id,
                "priority": "HIGH",
                "due_date": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
                "status": "IN_PROGRESS",
                "estimated_hours": 28.0,
                "actual_hours": 32.0
            },
            {
                "project_id": p1.id,
                "title": "Biometric Authentication Screen",
                "description": "FaceID and Fingerprint API integration with secure key storage.",
                "assigned_to": sneha.id,
                "priority": "MEDIUM",
                "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "status": "COMPLETED",
                "estimated_hours": 14.0,
                "actual_hours": 12.0
            },
            {
                "project_id": p1.id,
                "title": "App Store Submission Assets",
                "description": "Prepare localized privacy disclosures and screenshot bundles.",
                "assigned_to": priya.id,
                "priority": "LOW",
                "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
                "status": "TODO",
                "estimated_hours": 12.0,
                "actual_hours": 0.0
            },
            # College Management Portal (p2)
            {
                "project_id": p2.id,
                "title": "Payment Gateway Webhook Reconciliation",
                "description": "Automate Razorpay payment callback verification and receipt generation.",
                "assigned_to": amit.id,
                "priority": "HIGH",
                "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                "status": "COMPLETED",
                "estimated_hours": 16.0,
                "actual_hours": 15.0
            },
            {
                "project_id": p2.id,
                "title": "Faculty Workload Allocation Grid",
                "description": "Build lecture scheduling conflict detection matrix.",
                "assigned_to": sneha.id,
                "priority": "MEDIUM",
                "due_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
                "status": "IN_PROGRESS",
                "estimated_hours": 22.0,
                "actual_hours": 14.0
            },
            {
                "project_id": p2.id,
                "title": "Fee Structure PDF Export",
                "description": "Generate server-side annual fee breakdown statements.",
                "assigned_to": priya.id,
                "priority": "LOW",
                "due_date": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
                "status": "COMPLETED",
                "estimated_hours": 10.0,
                "actual_hours": 8.0
            },
            # AI Analytics Platform (p3)
            {
                "project_id": p3.id,
                "title": "Data Ingestion Pipeline for Semester Grades",
                "description": "Batch ETL parser supporting CSV and XLSX academic transcripts.",
                "assigned_to": priya.id,
                "priority": "HIGH",
                "due_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
                "status": "IN_PROGRESS",
                "estimated_hours": 24.0,
                "actual_hours": 10.0
            },
            {
                "project_id": p3.id,
                "title": "Interactive Retention Risk Visualizations",
                "description": "Implement D3 / Chart.js risk probability scatter plots.",
                "assigned_to": sneha.id,
                "priority": "MEDIUM",
                "due_date": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
                "status": "TODO",
                "estimated_hours": 18.0,
                "actual_hours": 0.0
            },
            # Website Redesign (p4)
            {
                "project_id": p4.id,
                "title": "WCAG 2.1 AA Accessibility Audit",
                "description": "Fix contrast ratios and screen reader aria-labels on public forms.",
                "assigned_to": priya.id,
                "priority": "HIGH",
                "due_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                "status": "IN_PROGRESS",
                "estimated_hours": 16.0,
                "actual_hours": 22.0
            },
            {
                "project_id": p4.id,
                "title": "DNS Cutover & CDN Cache Setup",
                "description": "Update Cloudflare edge DNS records and verify SSL certificates.",
                "assigned_to": rahul.id,
                "priority": "HIGH",
                "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "status": "TODO",
                "estimated_hours": 8.0,
                "actual_hours": 0.0
            },
        ]

        for t in tasks_data:
            db_task = models.Task(
                project_id=t["project_id"],
                title=t["title"],
                description=t["description"],
                assigned_to=t["assigned_to"],
                priority=t["priority"],
                due_date=t["due_date"],
                status=t["status"],
                estimated_hours=t["estimated_hours"],
                actual_hours=t["actual_hours"],
                created_at=datetime.utcnow()
            )
            db.add(db_task)

        db.commit()
        print(f"[SUCCESS] Seeded {len(users_data)} users, 4 projects, and {len(tasks_data)} tasks.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
