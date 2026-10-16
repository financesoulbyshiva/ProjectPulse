"""
Module: eda.py
Purpose: Generates exploratory data analysis (EDA) visualizations for ProjectPulse.
Outputs clean, professional figures suitable for academic & internship reports.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def generate_eda_visualizations(df: pd.DataFrame, results_dir: str):
    """
    Generates and saves the required EDA figures:
    1. delay_distribution.png
    2. completion_vs_delay.png
    3. budget_vs_delay.png
    4. workload_vs_delay.png
    """
    os.makedirs(results_dir, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")
    
    # 1. Delay Distribution
    plt.figure(figsize=(6, 5))
    counts = df["delay_status"].value_counts().sort_index()
    labels = ["On Time (0)", "Delayed (1)"]
    colors = ["#2563eb", "#e11d48"]
    bars = plt.bar(labels, counts, color=colors, width=0.5, edgecolor="#1e293b", linewidth=0.8)
    for bar in bars:
        h = bar.get_height()
        pct = (h / len(df)) * 100
        plt.text(bar.get_x() + bar.get_width() / 2, h + 5, f"{h} ({pct:.1f}%)", ha="center", va="bottom", fontsize=10, fontweight="bold")
    plt.title("Project Delivery Status Distribution", fontsize=12, fontweight="bold", pad=12)
    plt.ylabel("Number of Projects", fontsize=10)
    plt.ylim(0, max(counts) * 1.15)
    plt.tight_layout()
    p1 = os.path.join(results_dir, "delay_distribution.png")
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"EDA saved: {p1}")
    
    # 2. Completion vs Delay
    plt.figure(figsize=(7, 5))
    comp_pct = (df["completed_tasks"] / np.maximum(df["total_tasks"], 1)) * 100
    temp_df = df.copy()
    temp_df["completion_pct"] = comp_pct
    temp_df["Status"] = temp_df["delay_status"].map({0: "On Time", 1: "Delayed"})
    
    sns.boxplot(x="Status", y="completion_pct", data=temp_df, hue="Status", palette={"On Time": "#2563eb", "Delayed": "#e11d48"}, width=0.4, legend=False)
    sns.stripplot(x="Status", y="completion_pct", data=temp_df, color="black", alpha=0.2, jitter=0.2, size=4)
    plt.title("Project Completion Percentage vs Delay Status", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Delivery Status", fontsize=10)
    plt.ylabel("Completion Percentage (%)", fontsize=10)
    plt.tight_layout()
    p2 = os.path.join(results_dir, "completion_vs_delay.png")
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"EDA saved: {p2}")
    
    # 3. Budget vs Delay (Budget Utilization)
    plt.figure(figsize=(7, 5))
    temp_df["budget_util"] = (temp_df["spent_budget"] / np.maximum(temp_df["budget"], 1)) * 100
    sns.boxplot(x="Status", y="budget_util", data=temp_df, hue="Status", palette={"On Time": "#2563eb", "Delayed": "#e11d48"}, width=0.4, legend=False)
    sns.stripplot(x="Status", y="budget_util", data=temp_df, color="black", alpha=0.2, jitter=0.2, size=4)
    plt.title("Budget Utilization vs Delay Status", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Delivery Status", fontsize=10)
    plt.ylabel("Budget Utilization (%)", fontsize=10)
    plt.tight_layout()
    p3 = os.path.join(results_dir, "budget_vs_delay.png")
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"EDA saved: {p3}")
    
    # 4. Workload vs Delay
    plt.figure(figsize=(7, 5))
    sns.kdeplot(data=temp_df, x="avg_workload", hue="Status", palette={"On Time": "#2563eb", "Delayed": "#e11d48"}, fill=True, common_norm=False, alpha=0.4)
    plt.axvline(40.0, color="#d97706", linestyle="--", linewidth=1.5, label="Standard Capacity (40h/wk)")
    plt.title("Average Workload Density vs Delay Status", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Average Workload (Hours/Week/Developer)", fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.legend(title="")
    plt.tight_layout()
    p4 = os.path.join(results_dir, "workload_vs_delay.png")
    plt.savefig(p4, dpi=300)
    plt.close()
    print(f"EDA saved: {p4}")


if __name__ == "__main__":
    raw_csv = os.path.join(os.path.dirname(__file__), "..", "dataset", "project_data.csv")
    res_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    if os.path.exists(raw_csv):
        df = pd.read_csv(raw_csv)
        generate_eda_visualizations(df, res_dir)
