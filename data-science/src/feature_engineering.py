"""
Module: feature_engineering.py
Purpose: Reusable feature engineering pipeline for ProjectPulse ML system.
Computes domain-derived project management metrics while strictly preventing data leakage.
"""

from typing import Union, Dict, Any, List, Tuple
import pandas as pd
import numpy as np


# The exact feature columns consumed by the Random Forest model (ordered)
FEATURE_COLUMNS: List[str] = [
    "team_size",
    "total_tasks",
    "completed_tasks",
    "pending_tasks",
    "avg_workload",
    "estimated_hours",
    "actual_hours",
    "deadline_days_remaining",
    "previous_delays",
    "task_complexity",
    "dependencies",
    "completion_percentage",
    "budget_utilization",
    "workload_ratio",
    "hour_variance",
    "deadline_pressure",
    "dependency_risk"
]

TARGET_COLUMN = "delay_status"


def compute_derived_features(data: Union[pd.DataFrame, Dict[str, Any]]) -> pd.DataFrame:
    """
    Computes derived features with robust division-by-zero safeguards.
    
    Formulas:
    - completion_percentage = (completed_tasks / max(total_tasks, 1)) * 100
    - budget_utilization = (spent_budget / max(budget, 1.0)) * 100
    - workload_ratio = avg_workload / 40.0
    - hour_variance = actual_hours - estimated_hours
    - deadline_pressure = pending_tasks / max(deadline_days_remaining, 1.0)
    - dependency_risk = dependencies / max(total_tasks, 1)
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data.copy()

    # Division-by-zero safeguards
    total_tasks_safe = np.maximum(df["total_tasks"].astype(float), 1.0)
    budget_safe = np.maximum(df["budget"].astype(float), 1.0)
    deadline_safe = np.maximum(df["deadline_days_remaining"].astype(float), 1.0)

    # 1. Completion Percentage (%)
    df["completion_percentage"] = np.round(
        (df["completed_tasks"].astype(float) / total_tasks_safe) * 100.0, 2
    )

    # 2. Budget Utilization (%)
    df["budget_utilization"] = np.round(
        (df["spent_budget"].astype(float) / budget_safe) * 100.0, 2
    )

    # 3. Workload Ratio (relative to standard 40 hr work week)
    df["workload_ratio"] = np.round(
        df["avg_workload"].astype(float) / 40.0, 3
    )

    # 4. Hour Variance (actual logged - planned scope)
    df["hour_variance"] = np.round(
        df["actual_hours"].astype(float) - df["estimated_hours"].astype(float), 2
    )

    # 5. Deadline Pressure (tasks remaining per available runway day)
    df["deadline_pressure"] = np.round(
        df["pending_tasks"].astype(float) / deadline_safe, 3
    )

    # 6. Dependency Risk (ratio of blocked / dependency tasks)
    df["dependency_risk"] = np.round(
        df["dependencies"].astype(float) / total_tasks_safe, 3
    )

    return df


def prepare_features(
    df: pd.DataFrame, is_training: bool = False
) -> Union[Tuple[pd.DataFrame, pd.Series], pd.DataFrame]:
    """
    Prepares the final ordered feature matrix X (and target y if training).
    Confirms NO target leakage occurs into the predictor space.
    """
    df_transformed = compute_derived_features(df)
    
    # Assert all required feature columns exist
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df_transformed.columns]
    if missing_cols:
        raise ValueError(f"Missing required model features: {missing_cols}")
        
    X = df_transformed[FEATURE_COLUMNS].copy()

    # Guard: Target column must NEVER leak into X
    assert TARGET_COLUMN not in X.columns, f"Fatal: Target column '{TARGET_COLUMN}' leaked into feature matrix!"

    if is_training:
        if TARGET_COLUMN not in df.columns:
            raise ValueError(f"Training requires target column '{TARGET_COLUMN}' in dataset.")
        y = df[TARGET_COLUMN].copy()
        return X, y

    return X


if __name__ == "__main__":
    # Test sample row
    sample = {
        "team_size": 5,
        "total_tasks": 30,
        "completed_tasks": 20,
        "pending_tasks": 10,
        "avg_workload": 38.0,
        "estimated_hours": 600.0,
        "actual_hours": 420.0,
        "deadline_days_remaining": 25,
        "previous_delays": 1,
        "budget": 800000.0,
        "spent_budget": 520000.0,
        "task_complexity": 2.0,
        "dependencies": 4
    }
    
    X_test = prepare_features(pd.DataFrame([sample]), is_training=False)
    print("Feature Engineering successful!")
    print(f"Features generated ({len(FEATURE_COLUMNS)} columns):")
    print(X_test.iloc[0].to_dict())
