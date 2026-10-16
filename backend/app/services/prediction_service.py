"""
Service: prediction_service.py
Purpose: Integrates the Phase 3 Random Forest ML prediction pipeline into the FastAPI backend.
Reuses predict_project_risk() and cached get_model() without duplicating ML/feature logic.
"""

import os
import sys
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Resolve path to data-science/src
_current_dir = os.path.dirname(os.path.abspath(__file__))
# backend/app/services -> backend/app -> backend -> ProjectPulse root
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))
_ds_src_dir = os.path.join(_project_root, "data-science", "src")

if _ds_src_dir not in sys.path:
    sys.path.append(_ds_src_dir)

try:
    from predict import predict_project_risk, get_model
    _ml_available = True
except ImportError as exc:
    logger.error(f"Failed to import ML prediction modules from {_ds_src_dir}: {exc}")
    _ml_available = False


def init_ml_model():
    """
    Ensures the Random Forest model is loaded and cached in memory once at startup.
    Avoids retraining or reloading the model per request.
    """
    if not _ml_available:
        raise RuntimeError("Machine Learning subsystem is not available.")
    model_artifact = get_model()
    logger.info("ProjectPulse ML Random Forest model artifact successfully initialized.")
    return model_artifact


def get_risk_prediction(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes real-time inference using the trained Random Forest model.
    
    Args:
        project_data: Dictionary of 13 operational project features.
        
    Returns:
        Dictionary containing delay_probability, risk_score, risk_level, and expected_delay_days.
    """
    if not _ml_available:
        raise RuntimeError("ML model pipeline is unavailable.")
        
    return predict_project_risk(project_data)
