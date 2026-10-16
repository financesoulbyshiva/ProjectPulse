"""
Test script: test_ml.py
Validates the data science pipeline, model reloading, and prediction logic.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add src to path
src_dir = os.path.join(os.path.dirname(__file__), "src")
sys.path.append(src_dir)

from predict import predict_project_risk, get_model, MODEL_PATH
from feature_engineering import prepare_features, FEATURE_COLUMNS


def test_model_artifact_exists():
    assert os.path.exists(MODEL_PATH), f"Model artifact not found at {MODEL_PATH}"


def test_model_reloading():
    artifact = get_model(MODEL_PATH)
    assert "model" in artifact
    assert "feature_names" in artifact
    assert artifact["model_version"] == "1.0.0"
    assert hasattr(artifact["model"], "predict")
    assert hasattr(artifact["model"], "predict_proba")


def test_feature_engineering_no_leakage():
    sample = {
        "team_size": 4,
        "total_tasks": 20,
        "completed_tasks": 10,
        "pending_tasks": 10,
        "avg_workload": 40.0,
        "estimated_hours": 400.0,
        "actual_hours": 200.0,
        "deadline_days_remaining": 15,
        "previous_delays": 1,
        "budget": 500000.0,
        "spent_budget": 250000.0,
        "task_complexity": 2.0,
        "dependencies": 3
    }
    df = pd.DataFrame([sample])
    X = prepare_features(df, is_training=False)
    assert "delay_status" not in X.columns
    assert list(X.columns) == FEATURE_COLUMNS
    assert len(X.columns) == 17


def test_low_risk_scenario():
    sample = {
        "team_size": 8,
        "total_tasks": 50,
        "completed_tasks": 45,
        "pending_tasks": 5,
        "avg_workload": 25.0,
        "estimated_hours": 1000.0,
        "actual_hours": 800.0,
        "deadline_days_remaining": 60,
        "previous_delays": 0,
        "budget": 2000000.0,
        "spent_budget": 1400000.0,
        "task_complexity": 1.0,
        "dependencies": 1
    }
    result = predict_project_risk(sample)
    assert 0.0 <= result["delay_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert result["risk_level"] == "LOW"
    assert result["expected_delay_days"] >= 0.0


def test_high_risk_scenario():
    sample = {
        "team_size": 3,
        "total_tasks": 60,
        "completed_tasks": 8,
        "pending_tasks": 52,
        "avg_workload": 62.0,
        "estimated_hours": 1500.0,
        "actual_hours": 1300.0,
        "deadline_days_remaining": 5,
        "previous_delays": 5,
        "budget": 1200000.0,
        "spent_budget": 1150000.0,
        "task_complexity": 3.0,
        "dependencies": 18
    }
    result = predict_project_risk(sample)
    assert 0.0 <= result["delay_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert result["risk_level"] == "HIGH"
    assert result["expected_delay_days"] > 0.0


def test_generated_result_files():
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    required_files = [
        "metrics.json",
        "confusion_matrix.png",
        "feature_importance.png",
        "delay_distribution.png",
        "completion_vs_delay.png",
        "budget_vs_delay.png",
        "workload_vs_delay.png"
    ]
    for rf in required_files:
        fpath = os.path.join(results_dir, rf)
        assert os.path.exists(fpath), f"Missing required result file: {rf}"
        assert os.path.getsize(fpath) > 0, f"File {rf} is empty!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
