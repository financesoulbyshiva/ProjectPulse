"""
Module: train_model.py
Purpose: Complete, reproducible training pipeline for ProjectPulse Random Forest model.
Orchestrates:
1. Dataset loading
2. Data cleaning & validation
3. Exploratory Data Analysis (EDA) visualizations
4. Feature engineering (zero leakage)
5. Stratified 80/20 train/test split (seed=42)
6. Random Forest Classifier training
7. Formal evaluation and metrics generation
8. Artifact serialization (model.joblib)
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Ensure local modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from data_cleaning import clean_project_data
from feature_engineering import prepare_features, FEATURE_COLUMNS, TARGET_COLUMN
from eda import generate_eda_visualizations
from evaluate_model import evaluate_and_save_results


def run_training_pipeline():
    base_dir = os.path.dirname(current_dir)
    data_path = os.path.join(base_dir, "dataset", "project_data.csv")
    results_dir = os.path.join(base_dir, "results")
    models_dir = os.path.join(base_dir, "models")
    
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    print("=" * 60)
    print("ProjectPulse — Machine Learning Training Pipeline")
    print("=" * 60)
    
    # 1. Load Dataset
    print(f"\n[1/7] Loading dataset from: {data_path}")
    raw_df = pd.read_csv(data_path)
    print(f"      Raw records loaded: {len(raw_df)}")
    
    # 2. Data Cleaning
    print("\n[2/7] Running data cleaning & sanitization pipeline...")
    cleaned_df, clean_report = clean_project_data(raw_df)
    for k, v in clean_report.items():
        print(f"      - {k}: {v}")
        
    # 3. Exploratory Data Analysis (EDA)
    print("\n[3/7] Generating EDA visualizations in results/...")
    generate_eda_visualizations(cleaned_df, results_dir)
    
    # 4. Feature Engineering
    print("\n[4/7] Engineering derived domain features (leakage-free)...")
    X, y = prepare_features(cleaned_df, is_training=True)
    print(f"      Predictor matrix shape: {X.shape}")
    print(f"      Target vector shape:    {y.shape}")
    print(f"      Class distribution:\n{y.value_counts(normalize=True).to_dict()}")
    
    # 5. Stratified Train / Test Split
    print("\n[5/7] Executing Stratified Train/Test Split (80% Train, 20% Test, random_state=42)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )
    print(f"      Training set size: {len(X_train)} samples")
    print(f"      Holdout test size: {len(X_test)} samples")
    
    # 6. Train Random Forest Classifier
    print("\n[6/7] Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        criterion="gini",
        max_depth=6,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        bootstrap=True,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    print("      Model fitted successfully.")
    
    # 7. Model Evaluation & Visualization
    print("\n[7/7] Evaluating model against holdout test split...")
    metrics = evaluate_and_save_results(
        model=rf_model,
        X_test=X_test,
        y_test=y_test,
        feature_names=FEATURE_COLUMNS,
        results_dir=results_dir
    )
    
    # 8. Save Serialized Model Artifact
    model_artifact = {
        "model": rf_model,
        "feature_names": FEATURE_COLUMNS,
        "target_name": TARGET_COLUMN,
        "model_version": "1.0.0",
        "random_state": 42,
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 6,
            "criterion": "gini",
            "class_weight": "balanced"
        }
    }
    model_save_path = os.path.join(models_dir, "projectpulse_random_forest.joblib")
    joblib.dump(model_artifact, model_save_path)
    print(f"\nTrained model pipeline saved successfully to:\n{model_save_path}")
    print("=" * 60)
    print("Training Pipeline Complete!")
    print("=" * 60)
    
    return rf_model, metrics


if __name__ == "__main__":
    run_training_pipeline()
