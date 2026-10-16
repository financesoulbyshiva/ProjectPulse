from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table
)
from sqlalchemy.orm import relationship
from .database import Base

# Many-to-Many association table between Projects and Users (Team Members)
project_team_members = Table(
    "project_team_members",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="ROLE_PM")
    job_title = Column(String(100), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token_hash = Column(String(128), nullable=True, index=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    managed_projects = relationship(
        "Project",
        back_populates="manager",
        foreign_keys="Project.manager_id"
    )
    assigned_tasks = relationship(
        "Task",
        back_populates="assignee"
    )
    team_projects = relationship(
        "Project",
        secondary=project_team_members,
        back_populates="team_members"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(String(20), nullable=False)
    deadline = Column(String(20), nullable=False)
    budget = Column(Float, nullable=False, default=0.0)
    actual_cost = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="ON_TRACK")  # ON_TRACK, AT_RISK, COMPLETED, DELAYED
    complexity = Column(String(20), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH
    dependencies = Column(Integer, nullable=False, default=0)
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    manager = relationship(
        "User",
        foreign_keys=[manager_id],
        back_populates="managed_projects"
    )
    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    team_members = relationship(
        "User",
        secondary=project_team_members,
        back_populates="team_projects"
    )
    predictions = relationship(
        "Prediction",
        back_populates="project",
        cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    priority = Column(String(20), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH
    due_date = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="TODO")  # TODO, IN_PROGRESS, COMPLETED
    estimated_hours = Column(Float, nullable=False, default=0.0)
    actual_hours = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship(
        "Project",
        back_populates="tasks"
    )
    assignee = relationship(
        "User",
        back_populates="assigned_tasks"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    delay_probability = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    expected_delay_days = Column(Float, nullable=False)
    model_name = Column(String(100), nullable=False, default="Random Forest Classifier")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship(
        "Project",
        back_populates="predictions"
    )


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User")
