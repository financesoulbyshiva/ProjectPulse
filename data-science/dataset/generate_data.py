"""
Script: generate_data.py
Purpose: Synthesizes a realistic project management dataset for the ProjectPulse ML pipeline.
Target size: 420 records (between 300-500).
Notice: This dataset is simulated for the ProjectPulse internship prototype
and is not presented as real organizational project data.
"""

import os
import numpy as np
import pandas as pd

def generate_project_dataset(n_samples: int = 420, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)
    
    project_ids = [f"PRJ-{1001 + i}" for i in range(n_samples)]
    
    # 1. Team & Task Scale
    team_sizes = np.random.randint(2, 16, size=n_samples)
    total_tasks = np.random.randint(15, 85, size=n_samples)
    
    # Lifecycle completion fraction (0.05 to 0.95)
    progress_fractions = np.random.beta(a=1.8, b=1.8, size=n_samples)
    completed_tasks = np.clip((total_tasks * progress_fractions).astype(int), 1, total_tasks)
    pending_tasks = total_tasks - completed_tasks
    
    # 2. Hours and Workload
    task_hours_mean = np.random.uniform(18.0, 32.0, size=n_samples)
    estimated_hours = np.round(total_tasks * task_hours_mean, 1)
    
    # Slippage variance
    slippage_factor = np.clip(np.random.normal(loc=1.05, scale=0.28, size=n_samples), 0.65, 2.20)
    completed_fraction = completed_tasks / np.maximum(total_tasks, 1)
    actual_hours = np.round(estimated_hours * completed_fraction * slippage_factor, 1)
    
    # Average weekly workload per team member (hours/week)
    avg_workload = np.round(np.random.normal(loc=39.0, scale=8.5, size=n_samples), 1)
    avg_workload = np.clip(avg_workload, 18.0, 65.0)
    
    # 3. Timelines & Deadlines
    deadline_days_remaining = np.random.randint(3, 90, size=n_samples)
    
    # 4. History, Budget, Complexity
    previous_delays = np.clip(np.random.poisson(lam=1.2, size=n_samples), 0, 7)
    
    # Budget in INR: roughly 1,300 - 2,200 INR per estimated hour
    hourly_rate = np.random.uniform(1300.0, 2200.0, size=n_samples)
    budget = np.round(estimated_hours * hourly_rate, -3)
    
    # Spent budget: actual hours * rate + overhead
    cost_overhead_mult = np.random.uniform(0.95, 1.25, size=n_samples)
    spent_budget = np.round(actual_hours * hourly_rate * cost_overhead_mult, -2)
    
    # Task complexity: 1.0 (Low), 2.0 (Medium), 3.0 (High)
    task_complexity = np.round(np.random.choice([1.0, 2.0, 3.0], p=[0.25, 0.50, 0.25], size=n_samples), 1)
    
    # Dependencies: 5% to 35% of tasks have blocking dependencies
    dep_fraction = np.random.uniform(0.05, 0.35, size=n_samples)
    dependencies = np.clip((total_tasks * dep_fraction).astype(int), 0, 25)
    
    # 5. Delay Status Formulation (Latent risk logistic model with realistic compounding factors)
    comp_pct = completed_fraction * 100.0
    budget_util = (spent_budget / np.maximum(budget, 1.0)) * 100.0
    deadline_pressure = pending_tasks / np.maximum(deadline_days_remaining.astype(float), 1.0)
    workload_stress = (avg_workload - 40.0) / 10.0
    hour_burn_rate = (actual_hours / np.maximum(1.0, estimated_hours * completed_fraction)) - 1.0
    hour_burn_rate = np.nan_to_num(hour_burn_rate, nan=0.0)
    
    raw_z = (
        - 0.035 * (comp_pct - 50.0)
        + 0.50 * deadline_pressure
        + 0.45 * workload_stress
        + 0.70 * hour_burn_rate
        + 0.30 * previous_delays
        + 0.015 * np.maximum(0.0, budget_util - comp_pct)
        + 0.30 * (task_complexity - 2.0)
        + 0.04 * (dependencies - 6.0)
        - 1.25
        + np.random.normal(0, 0.35, size=n_samples)
    )
    
    prob = 1.0 / (1.0 + np.exp(-raw_z))
    delay_status = (prob >= 0.50).astype(int)
    
    df = pd.DataFrame({
        "project_id": project_ids,
        "team_size": team_sizes,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "avg_workload": avg_workload,
        "estimated_hours": estimated_hours,
        "actual_hours": actual_hours,
        "deadline_days_remaining": deadline_days_remaining,
        "previous_delays": previous_delays,
        "budget": budget,
        "spent_budget": spent_budget,
        "task_complexity": task_complexity,
        "dependencies": dependencies,
        "delay_status": delay_status
    })
    
    # Introduce controlled realistic noise to simulate real-world data collection anomalies:
    # 1. A few missing values in numerical columns
    df.loc[12, "actual_hours"] = np.nan
    df.loc[45, "previous_delays"] = np.nan
    df.loc[88, "avg_workload"] = np.nan
    
    # 2. A couple of duplicate rows
    duplicate_rows = df.iloc[[10, 20]].copy()
    df = pd.concat([df, duplicate_rows], ignore_index=True)
    
    # 3. An inconsistent pending_tasks discrepancy to test invariant verification
    df.loc[15, "pending_tasks"] = df.loc[15, "total_tasks"] + 5
    
    # 4. A slight negative value to test bound enforcement
    df.loc[30, "actual_hours"] = -12.5
    
    return df

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "project_data.csv")
    
    df = generate_project_dataset(n_samples=420, random_state=42)
    df.to_csv(out_path, index=False)
    
    print(f"Generated raw dataset with {len(df)} records saved to {out_path}")
    print(f"Delay Status distribution:\n{df['delay_status'].value_counts(dropna=False)}")
