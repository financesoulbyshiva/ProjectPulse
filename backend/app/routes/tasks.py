from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..security import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_MEMBER,
    ROLE_PM,
    can_manage_project,
    canonical_role,
    get_current_user,
    require_project_access,
    require_roles,
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("", response_model=List[schemas.TaskResponse])
def list_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status: TODO, IN_PROGRESS, COMPLETED"),
    priority: Optional[str] = Query(None, description="Filter by priority: LOW, MEDIUM, HIGH, CRITICAL"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned user ID"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return only tasks within the authenticated user's permitted scope."""
    query = db.query(models.Task)
    role = canonical_role(current_user.role)
    if role == ROLE_PM:
        query = query.join(models.Project).filter(models.Project.manager_id == current_user.id)
    elif role == ROLE_ANALYST:
        query = query.join(models.Project).filter(
            models.Project.team_members.any(models.User.id == current_user.id)
        )
    elif role == ROLE_MEMBER:
        query = query.filter(models.Task.assigned_to == current_user.id)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    if status and status != "All":
        query = query.filter(models.Task.status == status.upper().replace(" ", "_"))
    if priority and priority != "All":
        query = query.filter(models.Task.priority == priority.upper())
    if assigned_to is not None:
        query = query.filter(models.Task.assigned_to == assigned_to)
    return [crud.format_task_dict(task) for task in query.order_by(models.Task.id.desc()).all()]


@router.post("", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM)),
):
    project = require_project_access(db, current_user, task_in.project_id)
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project manager or an admin may create tasks.")

    if task_in.assigned_to is not None:
        assignee = crud.get_user_by_id(db, task_in.assigned_to)
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task assignee not found.")
        if canonical_role(assignee.role) not in {ROLE_MEMBER, ROLE_ANALYST}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tasks may only be assigned to team members or data analysts.")
        if all(member.id != assignee.id for member in project.team_members):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The assignee must belong to the project team.")

    return crud.create_task(db, task_in)


@router.patch("/{id}", response_model=schemas.TaskResponse)
def update_existing_task(
    id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = crud.get_task_by_id(db, id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {id} not found.")

    project = require_project_access(db, current_user, task.project_id)
    role = canonical_role(current_user.role)
    changes = task_update.model_dump(exclude_unset=True)
    if not can_manage_project(current_user, project):
        if role != ROLE_MEMBER or task.assigned_to != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only update tasks assigned to you.")
        if not changes or set(changes) - {"status", "actual_hours"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team members may only update task status and actual hours.")

    if task_update.assigned_to is not None:
        assignee = crud.get_user_by_id(db, task_update.assigned_to)
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task assignee not found.")
        if canonical_role(assignee.role) not in {ROLE_MEMBER, ROLE_ANALYST}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tasks may only be assigned to team members or data analysts.")
        if all(member.id != assignee.id for member in project.team_members):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The assignee must belong to the project team.")

    return crud.update_task(db, task, task_update)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM)),
):
    task = crud.get_task_by_id(db, id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {id} not found.")
    project = require_project_access(db, current_user, task.project_id)
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project manager or an admin may delete tasks.")
    crud.delete_task(db, task)
    return None
