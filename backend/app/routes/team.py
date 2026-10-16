from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..security import ROLE_ADMIN, get_current_user, require_roles, visible_team_user_ids
from ..services.email_service import send_account_verification_email

router = APIRouter(prefix="/api/team", tags=["Team"])


@router.get("", response_model=List[schemas.TeamMemberResponse])
def list_team_members(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return organization or project team information within the caller's scope."""
    return crud.get_team_members(db, visible_team_user_ids(db, current_user))


@router.post("", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    member_in: schemas.TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN)),
):
    """Create an unverified team-member account; only admins may provision users."""
    if crud.get_user_by_email(db, member_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{member_in.email}' already exists.",
        )

    user_create = schemas.UserCreate(
        name=member_in.name,
        email=member_in.email,
        role="ROLE_MEMBER",
        password=member_in.password,
    )
    user = crud.create_user(db, user_create, job_title=member_in.role)
    raw_token = crud.issue_email_verification_token(db, user)
    send_account_verification_email(user.email, user.name, raw_token)
    return user
