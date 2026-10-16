"""
Router: ai_analysis.py
Purpose: Exposes endpoints for ProjectPulse AI Risk Analyst:
- POST /api/projects/{project_id}/ai-risk-analysis
- GET /api/projects/{project_id}/ai-risk-analysis
- GET /api/projects/{project_id}/risk-history
- GET /api/projects/{project_id}/ai-report
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..security import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_PM,
    get_current_user,
    require_project_access,
    require_roles,
)
from ..services.ai_risk_analyst_service import (
    run_project_ai_risk_analysis,
    generate_full_project_report,
    GeminiServiceUnavailableError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["AI Risk Analyst"])


@router.post(
    "/{project_id}/ai-risk-analysis",
    response_model=schemas.AIRiskAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Risk Analysis",
    description="Executes Random Forest ML prediction, computes health score, grounds risk drivers, and generates prioritized action plan."
)
def generate_project_risk_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM, ROLE_ANALYST)),
):
    """
    POST /api/projects/{project_id}/ai-risk-analysis
    - Validates project existence.
    - Executes real Random Forest ML prediction.
    - Computes data-grounded risk drivers and recommendations.
    - Persists prediction snapshot and computes improvement delta.
    """
    require_project_access(db, current_user, project_id)

    try:
        analysis = run_project_ai_risk_analysis(db, project_id)
        return analysis
    except GeminiServiceUnavailableError as gemini_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(gemini_err)
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.error(f"Failed to generate AI risk analysis for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI risk analysis is temporarily unavailable. Your existing project risk prediction is still accessible."
        )


@router.get(
    "/{project_id}/ai-risk-analysis",
    response_model=schemas.AIRiskAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Latest AI Risk Analysis",
    description="Retrieves the AI risk analysis for a project."
)
def get_project_risk_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM, ROLE_ANALYST)),
):
    require_project_access(db, current_user, project_id)

    try:
        return run_project_ai_risk_analysis(db, project_id)
    except GeminiServiceUnavailableError as gemini_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(gemini_err)
        )
    except Exception as exc:
        logger.error(f"Error retrieving analysis for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI risk analysis."
        )


@router.get(
    "/{project_id}/risk-history",
    response_model=List[schemas.RiskHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get Project Risk History Trend",
    description="Returns chronological risk evaluation snapshots for historical trend visualization."
)
def get_project_risk_history(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM, ROLE_ANALYST)),
):
    require_project_access(db, current_user, project_id)

    preds = (
        db.query(models.Prediction)
        .filter(models.Prediction.project_id == project_id)
        .order_by(models.Prediction.created_at.asc())
        .all()
    )

    items = []
    for p in preds:
        items.append(schemas.RiskHistoryItem(
            id=p.id,
            date=p.created_at.strftime("%b %d, %H:%M"),
            score=p.risk_score,
            level=p.risk_level,
            delay_probability=round(p.delay_probability * 100, 1),
            expected_delay_days=p.expected_delay_days
        ))
    return items


@router.get(
    "/{project_id}/ai-report",
    response_model=schemas.FullAIReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Full Project AI Risk Report",
    description="Generates comprehensive executive project risk report suitable for review and export."
)
def get_full_project_ai_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ROLE_ADMIN, ROLE_PM, ROLE_ANALYST)),
):
    require_project_access(db, current_user, project_id)

    try:
        report = generate_full_project_report(db, project_id)
        return report
    except GeminiServiceUnavailableError as gemini_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(gemini_err)
        )
    except Exception as exc:
        logger.error(f"Error generating report for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI executive report."
        )
