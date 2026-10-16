"""
Module: data_cleaning.py
Purpose: Reusable data sanitization and validation pipeline for ProjectPulse.
Handles deduplication, missing value imputation, non-negativity bounds,
and project management invariant consistency.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


def clean_project_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans and standardizes raw project data.
    
    Returns:
        cleaned_df: Sanitized DataFrame ready for feature engineering
        cleaning_report: Summary dictionary of cleaning operations performed
    """
    report = {
        "initial_rows": len(df),
        "duplicates_removed": 0,
        "missing_imputed": {},
        "bounds_enforced": 0,
        "invariants_corrected": 0
    }
    
    cleaned = df.copy()
    
    # 1. Deduplication
    initial_count = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["project_id"], keep="first")
    report["duplicates_removed"] = initial_count - len(cleaned)
    
    # 2. Missing Value Imputation
    missing_counts = cleaned.isnull().sum()
    for col, count in missing_counts.items():
        if count > 0:
            report["missing_imputed"][col] = int(count)
            if col == "previous_delays":
                cleaned[col] = cleaned[col].fillna(0)
            elif col in ["avg_workload", "actual_hours", "estimated_hours", "budget", "spent_budget"]:
                median_val = cleaned[col].median()
                cleaned[col] = cleaned[col].fillna(median_val)
            else:
                cleaned[col] = cleaned[col].fillna(0)
                
    # 3. Domain Bounds & Non-negativity Enforcement
    # actual_hours & estimated_hours >= 0
    negative_hours = (cleaned["actual_hours"] < 0).sum()
    if negative_hours > 0:
        report["bounds_enforced"] += int(negative_hours)
        cleaned["actual_hours"] = cleaned["actual_hours"].clip(lower=0.0)
        
    cleaned["estimated_hours"] = cleaned["estimated_hours"].clip(lower=1.0)
    cleaned["budget"] = cleaned["budget"].clip(lower=1000.0)
    cleaned["spent_budget"] = cleaned["spent_budget"].clip(lower=0.0)
    cleaned["deadline_days_remaining"] = cleaned["deadline_days_remaining"].clip(lower=1)
    cleaned["team_size"] = cleaned["team_size"].clip(lower=1)
    
    # 4. Invariant Consistency Verification
    # Ensure completed_tasks <= total_tasks
    invalid_completed = (cleaned["completed_tasks"] > cleaned["total_tasks"]).sum()
    if invalid_completed > 0:
        cleaned["completed_tasks"] = np.minimum(cleaned["completed_tasks"], cleaned["total_tasks"])
        report["invariants_corrected"] += int(invalid_completed)
        
    # Invariant: completed_tasks + pending_tasks = total_tasks
    pending_mismatch = (cleaned["completed_tasks"] + cleaned["pending_tasks"] != cleaned["total_tasks"]).sum()
    if pending_mismatch > 0:
        report["invariants_corrected"] += int(pending_mismatch)
        cleaned["pending_tasks"] = np.maximum(0, cleaned["total_tasks"] - cleaned["completed_tasks"])
        
    # 5. Type Casting
    int_cols = [
        "team_size", "total_tasks", "completed_tasks", "pending_tasks",
        "deadline_days_remaining", "previous_delays", "dependencies"
    ]
    if "delay_status" in cleaned.columns:
        int_cols.append("delay_status")
        
    for col in int_cols:
        cleaned[col] = cleaned[col].round().astype(int)
        
    float_cols = ["avg_workload", "estimated_hours", "actual_hours", "budget", "spent_budget", "task_complexity"]
    for col in float_cols:
        cleaned[col] = cleaned[col].astype(float)
        
    # 6. Verification: Zero NaNs
    assert cleaned.isnull().sum().sum() == 0, "Data cleaning failed: NaNs remain in DataFrame!"
    
    report["final_rows"] = len(cleaned)
    return cleaned, report


if __name__ == "__main__":
    import os
    raw_csv = os.path.join(os.path.dirname(__file__), "..", "dataset", "project_data.csv")
    if os.path.exists(raw_csv):
        raw_df = pd.read_csv(raw_csv)
        clean_df, rep = clean_project_data(raw_df)
        print("Cleaning Report:")
        for k, v in rep.items():
            print(f"  {k}: {v}")
