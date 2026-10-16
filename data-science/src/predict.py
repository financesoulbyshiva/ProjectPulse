"""
Module: predict.py
Purpose: Reusable inference function for ProjectPulse ML risk prediction.
Consumes 13 operational raw project parameters, computes feature engineering transformations,
and outputs dynamic delay probability, risk score, risk level, and expected delay days.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

# Ensure local modules are accessible
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from feature_engineering import prepare_features

# Default model location
MODEL_PATH = os.path.join(os.path.dirname(current_dir), "models", "projectpulse_random_forest.joblib")

_LOADED_MODEL_ARTIFACT = None


def get_model(model_path: str = MODEL_PATH):
    """
    Lazy-loads and caches the trained Random Forest model artifact.
    """
    global _LOADED_MODEL_ARTIFACT
    if _LOADED_MODEL_ARTIFACT is None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Trained model artifact not found at {model_path}. Please run train_model.py first.")
        _LOADED_MODEL_ARTIFACT = joblib.load(model_path)
    return _LOADED_MODEL_ARTIFACT


def calculate_risk_score(
    prob: float,
    actual_hours: float,
    estimated_hours: float,
    spent_budget: float,
    budget: float,
    completed_tasks: int,
    total_tasks: int
) -> int:
    """
    Calculates dynamic composite Risk Score (0 - 100) combining model probability
    with operational hour strain and budget slippage strain.
    
    Formulas:
    Strain_hours = min(1.0, max(0.0, (actual_hours - estimated_hours) / max(1.0, estimated_hours)))
    Strain_budget = min(1.0, max(0.0, (spent_budget / max(1.0, budget)) - (completed_tasks / max(1, total_tasks))))
    Risk_Score = round(100 * (0.70 * prob + 0.15 * Strain_hours + 0.15 * Strain_budget))
    """
    est_safe = max(1.0, float(estimated_hours))
    total_safe = max(1, int(total_tasks))
    budget_safe = max(1.0, float(budget))
    
    strain_hours = min(1.0, max(0.0, (float(actual_hours) - float(estimated_hours)) / est_safe))
    comp_ratio = min(1.0, max(0.0, float(completed_tasks) / total_safe))
    budget_ratio = float(spent_budget) / budget_safe
    strain_budget = min(1.0, max(0.0, budget_ratio - comp_ratio))
    
    composite_raw = 100.0 * (0.70 * prob + 0.15 * strain_hours + 0.15 * strain_budget)
    score = int(round(np.clip(composite_raw, 0.0, 100.0)))
    return score


def calculate_risk_level(risk_score: int) -> str:
    """
    Categorizes Risk Score according to standardized project governance thresholds:
    0–30:   LOW
    31–60:  MEDIUM
    61–100: HIGH
    """
    if risk_score <= 30:
        return "LOW"
    elif risk_score <= 60:
        return "MEDIUM"
    else:
        return "HIGH"


def calculate_expected_delay(
    prob: float,
    pending_tasks: int,
    total_tasks: int,
    actual_hours: float,
    estimated_hours: float,
    previous_delays: int
) -> float:
    """
    Transparent estimation of schedule slippage (calendar days).
    Grounds delay forecast in remaining task velocity and historical inertia.
    """
    if prob < 0.25:
        return 0.0
        
    total_safe = max(1, int(total_tasks))
    remaining_ratio = min(1.0, max(0.0, float(pending_tasks) / total_safe))
    
    # Expected hours for completed work
    expected_completed_hours = max(1.0, float(estimated_hours) * (1.0 - remaining_ratio))
    burn_multiplier = min(2.5, max(1.0, float(actual_hours) / expected_completed_hours))
    
    delay_days = prob * (burn_multiplier * 14.0 + float(previous_delays) * 2.0)
    return round(float(delay_days), 1)


def predict_project_risk(project_data: Union[Dict[str, Any], pd.DataFrame], model_path: str = MODEL_PATH) -> Dict[str, Any]:
    """
    Primary reusable prediction entrypoint.
    
    Required input fields:
    - team_size (int)
    - total_tasks (int)
    - completed_tasks (int)
    - pending_tasks (int)
    - avg_workload (float)
    - estimated_hours (float)
    - actual_hours (float)
    - deadline_days_remaining (int)
    - previous_delays (int)
    - budget (float)
    - spent_budget (float)
    - task_complexity (float or int)
    - dependencies (int)
    
    Returns:
    {
        "delay_probability": float,
        "risk_score": int,
        "risk_level": str,
        "expected_delay_days": float
    }
    """
    artifact = get_model(model_path)
    model = artifact["model"]
    
    # If dict provided, wrap to single-row DataFrame
    if isinstance(project_data, dict):
        df_input = pd.DataFrame([project_data])
    else:
        df_input = project_data.copy()
        
    # Feature engineering pipeline
    X = prepare_features(df_input, is_training=False)
    
    # Random Forest probability of Delayed (class 1)
    probabilities = model.predict_proba(X)
    prob_delayed = float(probabilities[0][1])
    
    # Extract values for operational formulas
    row = df_input.iloc[0]
    actual_h = float(row.get("actual_hours", 0.0))
    est_h = float(row.get("estimated_hours", 1.0))
    spent_b = float(row.get("spent_budget", 0.0))
    bud = float(row.get("budget", 1.0))
    comp_t = int(row.get("completed_tasks", 0))
    tot_t = int(row.get("total_tasks", 1))
    pend_t = int(row.get("pending_tasks", 0))
    prev_d = int(row.get("previous_delays", 0))
    
    risk_score = calculate_risk_score(
        prob=prob_delayed,
        actual_hours=actual_h,
        estimated_hours=est_h,
        spent_budget=spent_b,
        budget=bud,
        completed_tasks=comp_t,
        total_tasks=tot_t
    )
    
    risk_level = calculate_risk_level(risk_score)
    
    expected_delay = calculate_expected_delay(
        prob=prob_delayed,
        pending_tasks=pend_t,
        total_tasks=tot_t,
        actual_hours=actual_h,
        estimated_hours=est_h,
        previous_delays=prev_d
    )
    
    return {
        "delay_probability": round(prob_delayed, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "expected_delay_days": expected_delay
    }


if __name__ == "__main__":
    print("Testing 3 canonical ProjectPulse risk scenarios...\n")
    
    # Scenario 1: Low-Risk Project
    # High completion, moderate workload, plenty of runway, 0 previous delays
    scenario_low = {
        "team_size": 6,
        "total_tasks": 40,
        "completed_tasks": 35,
        "pending_tasks": 5,
        "avg_workload": 28.0,
        "estimated_hours": 900.0,
        "actual_hours": 750.0,
        "deadline_days_remaining": 45,
        "previous_delays": 0,
        "budget": 1500000.0,
        "spent_budget": 1100000.0,
        "task_complexity": 1.0,
        "dependencies": 2
    }
    
    # Scenario 2: Medium-Risk Project
    # Moderate completion, normal workload, moderate deadline runway, 1 past delay
    scenario_medium = {
        "team_size": 5,
        "total_tasks": 50,
        "completed_tasks": 24,
        "pending_tasks": 26,
        "avg_workload": 40.0,
        "estimated_hours": 1200.0,
        "actual_hours": 650.0,
        "deadline_days_remaining": 28,
        "previous_delays": 1,
        "budget": 1800000.0,
        "spent_budget": 1050000.0,
        "task_complexity": 2.0,
        "dependencies": 6
    }
    
    # Scenario 3: High-Risk Project
    # Low completion, heavy workload, acute deadline pressure, multiple past delays, budget overrun
    scenario_high = {
        "team_size": 4,
        "total_tasks": 55,
        "completed_tasks": 12,
        "pending_tasks": 43,
        "avg_workload": 56.0,
        "estimated_hours": 1400.0,
        "actual_hours": 1100.0,
        "deadline_days_remaining": 8,
        "previous_delays": 4,
        "budget": 1600000.0,
        "spent_budget": 1550000.0,
        "task_complexity": 3.0,
        "dependencies": 15
    }
    
    print("1. LOW-RISK SCENARIO:")
    res_low = predict_project_risk(scenario_low)
    print(res_low)
    
    print("\n2. MEDIUM-RISK SCENARIO:")
    res_med = predict_project_risk(scenario_medium)
    print(res_med)
    
    print("\n3. HIGH-RISK SCENARIO:")
    res_high = predict_project_risk(scenario_high)
    print(res_high)
