from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..security import (
    ROLE_ADMIN,
    ROLE_PM,
    can_manage_project,
    canonical_role,
    accessible_projects_query,
    get_current_user,
    require_project_access,
    require_roles,
)
from .. import models

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=List[schemas.ProjectResponse])
def list_projects(
    status: Optional[str] = Query(None, description="Filter by status: ON_TRACK, AT_RISK, COMPLETED, DELAYED"),
    search: Optional[str] = Query(None, description="Search by project name or description"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retrieve all projects with dynamically calculated progress and team size."""
    query = accessible_projects_query(db, current_user)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Project.name.ilike(search_filter)) |
            (models.Project.description.ilike(search_filter))
        )
    projects = [crud.format_project_dict(project) for project in query.order_by(models.Project.id.desc()).all()]
    if status and status != "All":
        projects = [
            project for project in projects
            if project["status"].upper() == status.upper().replace(" ", "_")
        ]
    return projects


@router.post("", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM)),
):
    """Create a new project. Validates dates and positive budget constraints."""
    try:
        start_d = datetime.strptime(project_in.start_date, "%Y-%m-%d").date()
        dead_d = datetime.strptime(project_in.deadline, "%Y-%m-%d").date()
        if dead_d < start_d:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project deadline cannot be earlier than start date."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dates must be in YYYY-MM-DD format."
        )

    if project_in.budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project budget must be greater than zero."
        )

    if canonical_role(current_user.role) == ROLE_PM:
        if project_in.manager_id is not None and project_in.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project managers may only assign projects to themselves.")
        project_in.manager_id = current_user.id
    elif project_in.manager_id:
        manager = crud.get_user_by_id(db, project_in.manager_id)
        if not manager or canonical_role(manager.role) != ROLE_PM:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project manager with ID {project_in.manager_id} not found."
            )

    validate_project_members(db, project_in.team_member_ids or [])
    return crud.create_project(db, project_in)


def validate_project_members(db: Session, member_ids: List[int]) -> None:
    if not member_ids:
        return
    members = db.query(models.User).filter(models.User.id.in_(set(member_ids))).all()
    if len(members) != len(set(member_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more project members were not found.")
    if any(canonical_role(member.role) not in {"ROLE_MEMBER", "ROLE_ANALYST"} for member in members):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only team members and data analysts may be assigned to project teams.")


@router.get("/{id}", response_model=schemas.ProjectDetailResponse)
def get_project_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retrieve complete project details including associated tasks and team members."""
    project = require_project_access(db, current_user, id)

    project_data = crud.format_project_dict(project)
    project_tasks = project.tasks or []
    if canonical_role(current_user.role) == "ROLE_MEMBER":
        project_tasks = [task for task in project_tasks if task.assigned_to == current_user.id]
    project_data["tasks"] = [crud.format_task_dict(t) for t in project_tasks]
    project_data["team"] = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": canonical_role(u.role),
            "job_title": u.job_title,
        }
        for u in (project.team_members or [])
        if canonical_role(current_user.role) != "ROLE_MEMBER" or u.id == current_user.id
    ]
    return project_data


@router.patch("/{id}", response_model=schemas.ProjectResponse)
def update_existing_project(
    id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update project metadata, dates, budget, or status."""
    project = require_project_access(db, current_user, id)
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project manager or an admin may update this project.")

    update_fields = project_update.model_dump(exclude_unset=True)
    if "team_member_ids" in update_fields and update_fields["team_member_ids"] is not None:
        validate_project_members(db, update_fields["team_member_ids"])
    if "manager_id" in update_fields:
        if canonical_role(current_user.role) != ROLE_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an admin may reassign project managers.")
        manager_id = update_fields["manager_id"]
        manager = crud.get_user_by_id(db, manager_id) if manager_id is not None else None
        if manager_id is not None and (not manager or canonical_role(manager.role) != ROLE_PM):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projects may only be assigned to an existing project manager.")

    # Validate date updates if both or either provided
    new_start = project_update.start_date or project.start_date
    new_dead = project_update.deadline or project.deadline
    try:
        s_date = datetime.strptime(new_start, "%Y-%m-%d").date()
        d_date = datetime.strptime(new_dead, "%Y-%m-%d").date()
        if d_date < s_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project deadline cannot be earlier than start date."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dates must be in YYYY-MM-DD format."
        )

    if project_update.budget is not None and project_update.budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project budget must be greater than zero."
        )

    return crud.update_project(db, project, project_update)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a project and cascade delete associated tasks."""
    project = require_project_access(db, current_user, id)
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project manager or an admin may delete this project.")

    crud.delete_project(db, project)
    return None
