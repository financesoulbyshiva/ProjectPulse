from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import secrets
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas


# ==========================================
# AUTHENTICATION & PASSWORD UTILITIES
# ==========================================
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


def hash_secret(value: str) -> str:
    """Hash a sensitive short-lived secret (OTP code, reset token) using SHA-256."""
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


# ==========================================
# USER OPERATIONS
# ==========================================
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(
    db: Session,
    user: schemas.UserCreate,
    email_verified: bool = False,
    job_title: Optional[str] = None,
) -> models.User:
    hashed_pwd = hash_password(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        password_hash=hashed_pwd,
        role=user.role,
        job_title=job_title,
        email_verified=email_verified,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def issue_email_verification_token(db: Session, user: models.User, expires_in_hours: int = 24) -> str:
    """
    Generate a cryptographically secure 32-byte URL-safe token,
    hash it using SHA-256 for persistent database storage, and record 24-hour expiration.
    Invalidates any previous token for this user.
    """
    raw_token = secrets.token_urlsafe(32)
    user.email_verification_token_hash = hash_secret(raw_token)
    user.email_verification_expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    db.commit()
    db.refresh(user)
    return raw_token


def verify_email_token(db: Session, raw_token: str) -> tuple[bool, str, Optional[models.User]]:
    """
    Validate and consume an email verification token.
    Enforces expiration, token hashing, and single-use invalidation.
    """
    if not raw_token or not raw_token.strip():
        return False, "Verification token is required.", None

    token_hash = hash_secret(raw_token.strip())
    user = db.query(models.User).filter(
        models.User.email_verification_token_hash == token_hash
    ).first()

    if not user:
        return False, "This verification link is invalid or has already been used.", None

    if user.email_verification_expires_at and user.email_verification_expires_at < datetime.utcnow():
        return False, "This verification link has expired. Please request a new one.", user

    # Consume single-use token and mark verified
    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.commit()
    db.refresh(user)
    return True, "Email verified successfully.", user


def can_resend_verification(user: models.User, cooldown_seconds: int = 60) -> bool:
    """Check whether a user is past the cooldown period for resending verification emails."""
    if not user.email_verification_expires_at:
        return True
    time_left = (user.email_verification_expires_at - datetime.utcnow()).total_seconds()
    # 24 hours = 86400 seconds
    elapsed = 86400.0 - time_left
    if 0 <= elapsed < cooldown_seconds:
        return False
    return True



def get_all_users(db: Session) -> List[models.User]:
    return db.query(models.User).all()


def update_user_password(db: Session, user_id: int, new_password: str) -> Optional[models.User]:
    user = get_user_by_id(db, user_id)
    if user:
        user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)
    return user


# ==========================================
# PASSWORD RESET & OTP CODE OPERATIONS
# ==========================================
def create_password_reset_code(db: Session, email: str, code: str, expires_in_minutes: int = 10) -> models.PasswordResetCode:
    """Generate and store an active password reset OTP code, invalidating previous unused codes."""
    db.query(models.PasswordResetCode).filter(
        models.PasswordResetCode.email == email,
        models.PasswordResetCode.is_used == False
    ).update({"is_used": True})

    code_hash = hash_secret(code)
    now = datetime.utcnow()
    reset_code = models.PasswordResetCode(
        email=email,
        code_hash=code_hash,
        attempts=0,
        is_used=False,
        created_at=now,
        expires_at=now + timedelta(minutes=expires_in_minutes)
    )
    db.add(reset_code)
    db.commit()
    db.refresh(reset_code)
    return reset_code


def get_latest_reset_code(db: Session, email: str) -> Optional[models.PasswordResetCode]:
    """Retrieve the latest active password reset code for an email."""
    return db.query(models.PasswordResetCode).filter(
        models.PasswordResetCode.email == email,
        models.PasswordResetCode.is_used == False
    ).order_by(models.PasswordResetCode.id.desc()).first()


def create_password_reset_token(db: Session, user_id: int, token: str, expires_in_minutes: int = 15) -> models.PasswordResetToken:
    """Create and store a short-lived reset token for an authenticated user session."""
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user_id,
        models.PasswordResetToken.is_used == False
    ).update({"is_used": True})

    token_hash = hash_secret(token)
    now = datetime.utcnow()
    reset_tok = models.PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        is_used=False,
        created_at=now,
        expires_at=now + timedelta(minutes=expires_in_minutes)
    )
    db.add(reset_tok)
    db.commit()
    db.refresh(reset_tok)
    return reset_tok


def get_valid_reset_token(db: Session, token: str) -> Optional[models.PasswordResetToken]:
    """Retrieve an unused reset token matching the given secret."""
    token_hash = hash_secret(token)
    return db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token_hash == token_hash,
        models.PasswordResetToken.is_used == False
    ).first()


# ==========================================
# PROGRESS & STATUS DETERMINATION
# ==========================================
def calculate_project_progress(tasks: List[models.Task]) -> float:
    """Calculate progress percentage based on task completion."""
    if not tasks:
        return 0.0
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "COMPLETED")
    return round((completed / total) * 100.0, 1)


def determine_project_status(project: models.Project, tasks: List[models.Task]) -> str:
    """
    Sensible status logic:
    - All tasks completed -> COMPLETED
    - Deadline passed with incomplete tasks -> DELAYED
    - Deadline approaching (< 14 days) with progress < 60% or critical backlog -> AT_RISK
    - Otherwise -> ON_TRACK
    """
    if tasks and all(t.status == "COMPLETED" for t in tasks):
        return "COMPLETED"

    try:
        # Parse deadline (Format YYYY-MM-DD)
        deadline_date = datetime.strptime(project.deadline, "%Y-%m-%d").date()
        today = date.today()
        days_left = (deadline_date - today).days

        incomplete_tasks = [t for t in tasks if t.status != "COMPLETED"]

        if days_left < 0 and incomplete_tasks:
            return "DELAYED"

        progress = calculate_project_progress(tasks)
        has_critical_pending = any(t.priority in ("HIGH", "CRITICAL") for t in incomplete_tasks)

        if days_left <= 14 and (progress < 60.0 or has_critical_pending):
            return "AT_RISK"

    except Exception:
        pass

    return project.status or "ON_TRACK"


def format_project_dict(project: models.Project) -> Dict[str, Any]:
    """Helper to convert a Project ORM instance into response schema with dynamic progress."""
    tasks = project.tasks or []
    progress = calculate_project_progress(tasks)
    completed_count = sum(1 for t in tasks if t.status == "COMPLETED")
    team_members_list = [u.name for u in (project.team_members or [])]

    # Include manager in team members if not already present
    if project.manager and project.manager.name not in team_members_list:
        team_members_list.insert(0, project.manager.name)

    # Re-evaluate status dynamically
    dynamic_status = determine_project_status(project, tasks)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "start_date": project.start_date,
        "deadline": project.deadline,
        "budget": project.budget,
        "actual_cost": project.actual_cost,
        "status": dynamic_status,
        "complexity": project.complexity,
        "dependencies": project.dependencies,
        "manager_id": project.manager_id,
        "manager_name": project.manager.name if project.manager else None,
        "progress": progress,
        "total_tasks": len(tasks),
        "completed_tasks": completed_count,
        "team_size": len(team_members_list),
        "team_members": team_members_list,
        "created_at": project.created_at
    }


# ==========================================
# PROJECT OPERATIONS
# ==========================================
def get_projects(db: Session, status: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    query = db.query(models.Project)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Project.name.ilike(search_filter)) |
            (models.Project.description.ilike(search_filter))
        )

    projects = query.order_by(models.Project.id.desc()).all()
    formatted = [format_project_dict(p) for p in projects]

    if status and status != "All":
        formatted = [p for p in formatted if p["status"].upper() == status.upper().replace(" ", "_")]

    return formatted


def get_project_by_id(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def create_project(db: Session, project_in: schemas.ProjectCreate) -> Dict[str, Any]:
    db_project = models.Project(
        name=project_in.name,
        description=project_in.description,
        start_date=project_in.start_date,
        deadline=project_in.deadline,
        budget=project_in.budget,
        status=project_in.status.upper().replace(" ", "_"),
        complexity=project_in.complexity.upper(),
        dependencies=project_in.dependencies,
        manager_id=project_in.manager_id,
        created_at=datetime.utcnow()
    )

    # Attach team members if provided
    if project_in.team_member_ids:
        members = db.query(models.User).filter(models.User.id.in_(project_in.team_member_ids)).all()
        db_project.team_members = members

    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return format_project_dict(db_project)


def update_project(db: Session, project: models.Project, update_data: schemas.ProjectUpdate) -> Dict[str, Any]:
    update_dict = update_data.model_dump(exclude_unset=True)

    if "team_member_ids" in update_dict:
        member_ids = update_dict.pop("team_member_ids")
        if member_ids is not None:
            members = db.query(models.User).filter(models.User.id.in_(member_ids)).all()
            project.team_members = members

    for key, value in update_dict.items():
        if key == "status" and value:
            value = value.upper().replace(" ", "_")
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return format_project_dict(project)


def delete_project(db: Session, project: models.Project) -> None:
    db.delete(project)
    db.commit()


# ==========================================
# TASK OPERATIONS
# ==========================================
def format_task_dict(task: models.Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "project_name": task.project.name if task.project else None,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "assignee_name": task.assignee.name if task.assignee else None,
        "priority": task.priority,
        "due_date": task.due_date,
        "status": task.status,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "created_at": task.created_at
    }


def get_tasks(
    db: Session,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None
) -> List[Dict[str, Any]]:
    query = db.query(models.Task)

    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    if status and status != "All":
        query = query.filter(models.Task.status == status.upper().replace(" ", "_"))
    if priority and priority != "All":
        query = query.filter(models.Task.priority == priority.upper())
    if assigned_to is not None:
        query = query.filter(models.Task.assigned_to == assigned_to)

    tasks = query.order_by(models.Task.id.desc()).all()
    return [format_task_dict(t) for t in tasks]


def get_task_by_id(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def create_task(db: Session, task_in: schemas.TaskCreate) -> Dict[str, Any]:
    db_task = models.Task(
        project_id=task_in.project_id,
        title=task_in.title,
        description=task_in.description,
        assigned_to=task_in.assigned_to,
        priority=task_in.priority.upper(),
        due_date=task_in.due_date,
        status=task_in.status.upper().replace(" ", "_"),
        estimated_hours=task_in.estimated_hours,
        actual_hours=task_in.actual_hours,
        created_at=datetime.utcnow()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return format_task_dict(db_task)


def update_task(db: Session, task: models.Task, update_data: schemas.TaskUpdate) -> Dict[str, Any]:
    update_dict = update_data.model_dump(exclude_unset=True)

    for key, value in update_dict.items():
        if key == "status" and value:
            value = value.upper().replace(" ", "_")
        elif key == "priority" and value:
            value = value.upper()
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return format_task_dict(task)


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()


# ==========================================
# TEAM OPERATIONS & WORKLOAD
# ==========================================
def get_team_members(
    db: Session, user_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    query = db.query(models.User)
    if user_ids is not None:
        query = query.filter(models.User.id.in_(user_ids))
    users = query.all()
    team_data = []

    for user in users:
        # Active projects: projects managed or contributed where status != COMPLETED
        managed_p = [p for p in user.managed_projects if p.status != "COMPLETED"]
        team_p = [p for p in user.team_projects if p.status != "COMPLETED"]
        all_active_p_ids = {p.id for p in managed_p + team_p}

        tasks = user.assigned_tasks or []
        assigned_tasks_count = sum(1 for t in tasks if t.status != "COMPLETED")
        completed_tasks_count = sum(1 for t in tasks if t.status == "COMPLETED")

        # Sum allocated hours for active/incomplete tasks
        allocated_hours = sum(t.estimated_hours for t in tasks if t.status != "COMPLETED")
        capacity_hours = 40.0

        if allocated_hours > 40.0:
            workload = "HIGH"
        elif allocated_hours >= 20.0:
            workload = "MEDIUM"
        else:
            workload = "LOW"

        team_data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.job_title or user.role,
            "active_projects": len(all_active_p_ids),
            "assigned_tasks": assigned_tasks_count,
            "completed_tasks": completed_tasks_count,
            "workload": workload,
            "capacity_hours": capacity_hours,
            "allocated_hours": allocated_hours
        })

    return team_data


# ==========================================
# ANALYTICS OPERATIONS
# ==========================================
def get_analytics(
    db: Session, project_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    project_query = db.query(models.Project)
    task_query = db.query(models.Task)
    if project_ids is not None:
        project_query = project_query.filter(models.Project.id.in_(project_ids))
        task_query = task_query.filter(models.Task.project_id.in_(project_ids))
    projects = project_query.all()
    tasks = task_query.all()

    total_projects = len(projects)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "COMPLETED")

    # Evaluate dynamic status and progress for each project
    status_counts = {"ON_TRACK": 0, "AT_RISK": 0, "COMPLETED": 0, "DELAYED": 0}
    progress_sum = 0.0

    total_budget = sum(p.budget for p in projects)
    total_spent = sum(p.actual_cost for p in projects)

    total_estimated_hours = sum(t.estimated_hours for t in tasks)
    total_actual_hours = sum(t.actual_hours for t in tasks)

    for p in projects:
        p_tasks = [t for t in tasks if t.project_id == p.id]
        p_prog = calculate_project_progress(p_tasks)
        progress_sum += p_prog
        p_status = determine_project_status(p, p_tasks)
        if p_status in status_counts:
            status_counts[p_status] += 1
        else:
            status_counts[p_status] = 1

    active_projects = total_projects - status_counts.get("COMPLETED", 0)
    completed_projects = status_counts.get("COMPLETED", 0)
    delayed_projects = status_counts.get("DELAYED", 0)

    overall_completion = round((completed_tasks / total_tasks * 100.0), 1) if total_tasks > 0 else 0.0
    avg_progress = round(progress_sum / total_projects, 1) if total_projects > 0 else 0.0

    budget_utilization = round((total_spent / total_budget * 100.0), 1) if total_budget > 0 else 0.0

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "delayed_projects": delayed_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overall_completion": overall_completion,
        "average_project_progress": avg_progress,
        "status_distribution": status_counts,
        "hours_summary": {
            "total_estimated_hours": total_estimated_hours,
            "total_actual_hours": total_actual_hours,
            "hours_variance": round(total_actual_hours - total_estimated_hours, 1)
        },
        "budget_summary": {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "utilization_rate": budget_utilization
        }
    }
