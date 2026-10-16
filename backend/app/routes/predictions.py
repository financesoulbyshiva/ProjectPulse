"""
Router: predictions.py
Purpose: Exposes POST /api/predict-risk for real-time project schedule delay prediction.
Validates operational inputs via Pydantic, delegates inference to Phase 3 ML model,
and persists Prediction records when project_id is provided.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..security import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_PM,
    canonical_role,
    get_current_user,
    require_project_access,
)
from ..services.prediction_service import get_risk_prediction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Predictions"])


@router.post(
    "/predict-risk",
    response_model=schemas.PredictionResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Predict Project Delay Risk",
    description="Calculates delay probability, risk score, risk level, and expected delay days using the trained Random Forest model."
)
def predict_project_risk_endpoint(
    payload: schemas.PredictionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    POST /api/predict-risk endpoint.
    - Validates operational project variables.
    - Reuses Phase 3 ML Random Forest model.
    - Persists Prediction record if project_id is provided and verified.
    """
    # 1. Check optional project_id existence
    project: Optional[models.Project] = None
    if payload.project_id is not None:
        if canonical_role(current_user.role) not in {ROLE_ADMIN, ROLE_PM, ROLE_ANALYST}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project risk predictions are unavailable for this role.")
        project = require_project_access(db, current_user, payload.project_id)

    # 2. Extract operational features for ML model (excluding project_id)
    features_dict = payload.model_dump(exclude={"project_id"})

    # 3. Execute inference via Prediction Service
    try:
        prediction_result = get_risk_prediction(features_dict)
    except Exception as exc:
        logger.error(f"Internal ML inference failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute delay prediction due to an internal server error."
        )

    # 4. Persist Prediction record if project_id was supplied and validated
    if project is not None:
        try:
            db_prediction = models.Prediction(
                project_id=project.id,
                delay_probability=prediction_result["delay_probability"],
                risk_score=prediction_result["risk_score"],
                risk_level=prediction_result["risk_level"],
                expected_delay_days=prediction_result["expected_delay_days"],
                model_name="Random Forest Classifier"
            )
            db.add(db_prediction)
            db.commit()
            db.refresh(db_prediction)
            prediction_result["project_id"] = project.id
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to persist prediction history: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Prediction computed but failed to persist history record."
            )

    return prediction_result
