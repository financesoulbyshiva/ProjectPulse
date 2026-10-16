from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from .. import models
from ..security import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_PM,
    accessible_projects_query,
    require_roles,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("", response_model=schemas.AnalyticsResponse)
def get_system_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM, ROLE_ANALYST)),
):
    """
    Retrieve real-time project management analytics calculated dynamically
    from database project, task, and team records.
    """
    project_ids = [project.id for project in accessible_projects_query(db, current_user).all()]
    return crud.get_analytics(db, project_ids=project_ids)
