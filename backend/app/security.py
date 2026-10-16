import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Callable, Optional, Sequence

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from .database import get_db

logger = logging.getLogger(__name__)

ROLE_ADMIN = "ROLE_ADMIN"
ROLE_PM = "ROLE_PM"
ROLE_MEMBER = "ROLE_MEMBER"
ROLE_ANALYST = "ROLE_ANALYST"
ALL_ROLES = {ROLE_ADMIN, ROLE_PM, ROLE_MEMBER, ROLE_ANALYST}
PUBLIC_SIGNUP_ROLES = {ROLE_PM, ROLE_MEMBER, ROLE_ANALYST}
ACCESS_TOKEN_TTL_SECONDS = 8 * 60 * 60

_development_secret = secrets.token_bytes(32)
_bearer = HTTPBearer(auto_error=False)


def canonical_role(role: Optional[str]) -> str:
    """Normalize stored or display-role values to one of the supported backend roles."""
    if not role:
        return ROLE_MEMBER
    normalized = str(role).strip()
    aliases = {
        "ADMIN": ROLE_ADMIN,
        "ROLE_ADMIN": ROLE_ADMIN,
        "ADMINISTRATOR": ROLE_ADMIN,
        "PROJECT MANAGER": ROLE_PM,
        "ROLE_PM": ROLE_PM,
        "TEAM MEMBER": ROLE_MEMBER,
        "ROLE_MEMBER": ROLE_MEMBER,
        "MEMBER": ROLE_MEMBER,
        "DATA ANALYST": ROLE_ANALYST,
        "ROLE_ANALYST": ROLE_ANALYST,
        "ANALYST": ROLE_ANALYST,
    }
    if normalized.upper() in aliases:
        return aliases[normalized.upper()]
    return normalized if normalized in ALL_ROLES else ROLE_MEMBER


def validate_security_config() -> None:
    configured_secret = os.getenv("SECRET_KEY")
    if configured_secret and len(configured_secret.encode("utf-8")) >= 32:
        return
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("SECRET_KEY must be configured with at least 32 characters in production.")
    if configured_secret:
        raise RuntimeError("SECRET_KEY must contain at least 32 characters.")
    logger.warning("SECRET_KEY is unset; using a process-local development key. Sessions expire on restart.")


def _signing_secret() -> bytes:
    configured_secret = os.getenv("SECRET_KEY")
    if configured_secret:
        if len(configured_secret.encode("utf-8")) < 32:
            raise RuntimeError("SECRET_KEY must contain at least 32 characters.")
        return configured_secret.encode("utf-8")
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("SECRET_KEY must be configured in production.")
    return _development_secret


def _encode_token_payload(payload: dict) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).rstrip(b"=").decode("ascii")


def create_access_token(user_id: int, expires_in: int = ACCESS_TOKEN_TTL_SECONDS) -> str:
    payload = _encode_token_payload({"sub": user_id, "exp": int(time.time()) + expires_in})
    signature = hmac.new(_signing_secret(), payload.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{payload}.{encoded_signature}"


def _decode_access_token(token: str) -> int:
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
        expected_signature = hmac.new(
            _signing_secret(), payload_part.encode("ascii"), hashlib.sha256
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            signature_part + "=" * (-len(signature_part) % 4)
        )
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid access token signature.")
        payload = json.loads(
            base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4))
        )
        user_id = payload.get("sub")
        if not isinstance(user_id, int) or payload.get("exp", 0) <= int(time.time()):
            raise ValueError("Access token is expired or malformed.")
        return user_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_access_token(credentials.credentials)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The account is unavailable or its email is not verified.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*allowed_roles: str) -> Callable:
    allowed = set(allowed_roles)

    def role_dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if canonical_role(user.role) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return role_dependency


def accessible_projects_query(db: Session, user: models.User):
    query = db.query(models.Project)
    role = canonical_role(user.role)
    if role == ROLE_ADMIN:
        return query
    if role == ROLE_PM:
        return query.filter(models.Project.manager_id == user.id)
    if role == ROLE_ANALYST:
        return query.filter(models.Project.team_members.any(models.User.id == user.id))
    return query.filter(or_(
        models.Project.team_members.any(models.User.id == user.id),
        models.Project.tasks.any(models.Task.assigned_to == user.id),
    ))


def get_accessible_project(
    db: Session, user: models.User, project_id: int
) -> Optional[models.Project]:
    return accessible_projects_query(db, user).filter(models.Project.id == project_id).first()


def require_project_access(
    db: Session, user: models.User, project_id: int
) -> models.Project:
    project = get_accessible_project(db, user, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found.",
        )
    return project


def can_manage_project(user: models.User, project: models.Project) -> bool:
    return canonical_role(user.role) == ROLE_ADMIN or (
        canonical_role(user.role) == ROLE_PM and project.manager_id == user.id
    )


def visible_team_user_ids(db: Session, user: models.User) -> Optional[Sequence[int]]:
    role = canonical_role(user.role)
    if role == ROLE_ADMIN:
        return None
    if role == ROLE_MEMBER:
        return [user.id]

    projects = accessible_projects_query(db, user).all()
    project_ids = [project.id for project in projects]
    if not project_ids:
        return [user.id]
    member_ids = {
        row[0]
        for row in db.query(models.project_team_members.c.user_id)
        .filter(models.project_team_members.c.project_id.in_(project_ids))
        .all()
    }
    manager_ids = {project.manager_id for project in projects if project.manager_id is not None}
    return sorted(member_ids | manager_ids | {user.id})
