"""
Module: evaluate_model.py
Purpose: Formal evaluation of ProjectPulse Machine Learning model.
Computes real classification metrics, generates confusion matrix, and feature importance plots.
Never fabricates metrics.
"""

import os
import json
from typing import Dict, Any, List
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend for server execution
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


def evaluate_and_save_results(
    model: Any,
    X_test: Any,
    y_test: Any,
    feature_names: List[str],
    results_dir: str
) -> Dict[str, Any]:
    """
    Computes genuine holdout metrics, saves metrics.json, and generates visualization figures.
    """
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # 2. Compute Real Metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    metrics = {
        "model_type": "RandomForestClassifier",
        "n_test_samples": len(y_test),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {
            "true_negative": cm[0][0],
            "false_positive": cm[0][1],
            "false_negative": cm[1][0],
            "true_positive": cm[1][1]
        },
        "classification_report": report_dict
    }
    
    # Save metrics.json
    metrics_path = os.path.join(results_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Metrics saved to {metrics_path}")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    
    # 3. Plot Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["On Time (0)", "Delayed (1)"],
        yticklabels=["On Time (0)", "Delayed (1)"]
    )
    plt.title("Project Delay Prediction — Confusion Matrix", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Predicted Label", fontsize=10)
    plt.ylabel("Actual Ground Truth", fontsize=10)
    plt.tight_layout()
    cm_path = os.path.join(results_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Confusion matrix plot saved to {cm_path}")
    
    # 4. Plot Feature Importance
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        sorted_features = [feature_names[i] for i in indices]
        sorted_importances = importances[indices]
        
        # Save feature importance to metrics
        metrics["feature_importance_ranking"] = {
            sorted_features[i]: round(float(sorted_importances[i]), 4)
            for i in range(len(sorted_features))
        }
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        plt.figure(figsize=(9, 6))
        colors = plt.cm.Blues(np.linspace(0.85, 0.35, len(sorted_features)))
        bars = plt.barh(range(len(sorted_features)), sorted_importances[::-1], color=colors[::-1])
        plt.yticks(range(len(sorted_features)), sorted_features[::-1], fontsize=9)
        plt.xlabel("Gini Feature Importance (MDI)", fontsize=10)
        plt.title("Random Forest — Feature Importance Ranking", fontsize=12, fontweight="bold", pad=12)
        plt.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()
        fi_path = os.path.join(results_dir, "feature_importance.png")
        plt.savefig(fi_path, dpi=300)
        plt.close()
        print(f"Feature importance plot saved to {fi_path}")

    return metrics
