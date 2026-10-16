# ProjectPulse — Data Science & Machine Learning Pipeline

**Track. Analyze. Predict. Deliver.**  
**Subsystem:** Data Science + Predictive Delay Risk Engine  
**Release:** Phase 3 (Internship MVP)

---

## 1. Project Objective
ProjectPulse is an AI-powered project management platform integrating predictive data science into project oversight. The objective of this Data Science subsystem is to provide **early, explainable, probabilistic detection of project schedule delays** before critical deadlines are breached.

Instead of arbitrary risk scores or opaque deep-learning models, ProjectPulse implements a robust, reproducible **Random Forest Classification** and risk modeling pipeline.

---

## 2. Dataset Profile & Disclaimer

> [!IMPORTANT]
> **Simulated Data Notice:** This dataset is realistically simulated for the ProjectPulse internship prototype to model software engineering sprint and delivery dynamics. It is not presented as real organizational project data.

- **Storage Location:** `data-science/dataset/project_data.csv`
- **Total Records:** 420 project snapshots (after sanitizing 422 raw observation rows)
- **Class Balance:**
  - `0 (On Time)`: 246 projects (58.57%)
  - `1 (Delayed)`: 174 projects (41.43%)
- **Data Generator:** `data-science/dataset/generate_data.py` (fixed seed `42` for exact reproducibility)

---

## 3. Feature Descriptions & Schema

### Raw Operational Predictors (13 inputs)
1. `team_size`: Total developers/designers assigned to project ($[2, 16]$)
2. `total_tasks`: Total planned work items ($[15, 85]$)
3. `completed_tasks`: Tasks marked `Completed` ($[0, \text{total\_tasks}]$)
4. `pending_tasks`: Tasks in `To Do` or `In Progress`
5. `avg_workload`: Average weekly hours assigned per contributor ($[15.0, 68.0]$)
6. `estimated_hours`: Total planned engineering hours
7. `actual_hours`: Cumulative hours logged to date
8. `deadline_days_remaining`: Calendar days until scheduled deadline ($[2, 90]$)
9. `previous_delays`: Count of past late deliverables or missed milestones ($[0, 8]$)
10. `budget`: Approved project capital in INR ($₹1,00,000$ to $₹25,00,000$)
11. `spent_budget`: Cumulative financial expenditure in INR
12. `task_complexity`: Mean complexity rating ($1.0 = \text{Low}, 2.0 = \text{Medium}, 3.0 = \text{High}$)
13. `dependencies`: Count of tasks blocked by external tasks ($[0, 25]$)

### Target Variable
- `delay_status`: Binary integer target
  - `0`: Project completed on schedule.
  - `1`: Project breached scheduled delivery deadline.

---

## 4. Data Cleaning Pipeline
Implemented in `data-science/src/data_cleaning.py`:
- **Deduplication:** Identified and dropped duplicate snapshot entries.
- **Missing Value Imputation:** Imputed missing values using domain medians (`avg_workload`, `actual_hours`) or zero (`previous_delays`).
- **Non-negativity & Domain Bounds:** Enforced $hours \ge 0$, $budget > 0$, $deadline \ge 1$ day, $team\_size \ge 1$.
- **Invariant Consistency Verification:** Enforced $completed\_tasks + pending\_tasks = total\_tasks$.
- **Zero-NaN Verification:** Confirmed 100% clean data with 0 missing values before feature transformation.

---

## 5. Exploratory Data Analysis (EDA)
Generated publication-grade figures saved to `data-science/results/`:
1. `delay_distribution.png`: Bar chart displaying 58.6% On Time vs 41.4% Delayed class balance.
2. `completion_vs_delay.png`: Box plot showing distinct lower completion percentage distributions for delayed initiatives.
3. `budget_vs_delay.png`: Box plot examining budget utilization pressure relative to delivery success.
4. `workload_vs_delay.png`: Kernel Density Estimation (KDE) plot highlighting sharp risk escalation when weekly developer workload exceeds 40 hours.

---

## 6. Feature Engineering (Zero Data Leakage)
Implemented in `data-science/src/feature_engineering.py`:
Six domain-engineered metrics are calculated with division-by-zero safeguards:
- **`completion_percentage`**: $\frac{completed\_tasks}{\max(total\_tasks, 1)} \times 100.0$
- **`budget_utilization`**: $\frac{spent\_budget}{\max(budget, 1.0)} \times 100.0$
- **`workload_ratio`**: $\frac{avg\_workload}{40.0}$ (relative to 40 hr standard week)
- **`hour_variance`**: $actual\_hours - estimated\_hours$
- **`deadline_pressure`**: $\frac{pending\_tasks}{\max(deadline\_days\_remaining, 1.0)}$
- **`dependency_risk`**: $\frac{dependencies}{\max(total\_tasks, 1)}$

**Anti-Leakage Guard:** The target `delay_status` is strictly isolated and never included in the predictor matrix. Total model input vector size = 17 features.

---

## 7. Machine Learning Model & Training

### Model Architecture
- **Algorithm:** Scikit-Learn `RandomForestClassifier`
- **Parameters:**
  - `n_estimators = 100`
  - `criterion = "gini"`
  - `max_depth = 6` (constrained tree depth to prevent leaf overfitting)
  - `min_samples_split = 5`
  - `min_samples_leaf = 2`
  - `class_weight = "balanced"`
  - `random_state = 42` (deterministic seed)

### Train/Test Split
- **Partition:** 80% Training ($N = 336$), 20% Holdout Test ($N = 84$)
- **Stratification:** Stratified by `delay_status` to maintain identical class ratios across partitions.

---

## 8. Actual Evaluation Metrics
Evaluated on the held-out test split ($N = 84$) and recorded in `data-science/results/metrics.json`:

| Metric | Score | Performance Context |
| :--- | :--- | :--- |
| **Accuracy** | **84.52%** | Overall correct delay classifications |
| **Precision** | **78.95%** | Minimizes false alarm disruptions for project managers |
| **Recall (Sensitivity)** | **85.71%** | Prioritizes catching genuine impending schedule breaches |
| **F1-Score** | **82.19%** | Harmonic balance between Precision and Recall |

### Confusion Matrix ($N = 84$)
| | Predicted On Time (`0`) | Predicted Delayed (`1`) |
| :--- | :---: | :---: |
| **Actual On Time (`0`)** | **41** (True Negative) | **8** (False Positive) |
| **Actual Delayed (`1`)** | **5** (False Negative) | **30** (True Positive) |

Saved visualization: `data-science/results/confusion_matrix.png`

---

## 9. Feature Importance Ranking
Extracted from Random Forest Gini impurity reduction (MDI) and visualized in `data-science/results/feature_importance.png`:

1. `completion_percentage` (0.1995) — Primary indicator of realized progress
2. `deadline_pressure` (0.1483) — Pending tasks per runway day remaining
3. `pending_tasks` (0.1409) — Absolute outstanding deliverable volume
4. `budget_utilization` (0.0678) — Capital expenditure pace
5. `workload_ratio` (0.0591) — Team operational overload vs 40h capacity
6. `hour_variance` (0.0557) — Actual hours outrunning estimated hours
7. `avg_workload` (0.0520) — Weekly hours logged per developer
8. `completed_tasks` (0.0474) — Realized delivery volume
9. `actual_hours` (0.0387) — Total logged effort
10. `deadline_days_remaining` (0.0329) — Available delivery runway
11. `dependency_risk` (0.0328) — Proportion of dependency-blocked work
12. `previous_delays` (0.0280) — Historical velocity friction
13. `dependencies` (0.0265) — Blocking items
14. `total_tasks` (0.0242) — Project scale
15. `estimated_hours` (0.0231) — Planned scope size
16. `team_size` (0.0147) — Available resource headcount
17. `task_complexity` (0.0085) — Mean intellectual/technical difficulty

---

## 10. Risk Score & Expected Delay Methodology

### Dynamic Risk Score ($0 - 100$)
Combines model probability with real-time operational strain:
$$\text{Strain}_{\text{hours}} = \min\left(1.0, \; \max\left(0.0, \; \frac{actual\_hours - estimated\_hours}{\max(1.0, estimated\_hours)}\right)\right)$$
$$\text{Strain}_{\text{budget}} = \min\left(1.0, \; \max\left(0.0, \; \frac{spent\_budget}{\max(1.0, budget)} - \frac{completed\_tasks}{\max(1, total\_tasks)}\right)\right)$$
$$\text{Risk Score} = \text{round}\Big(100 \times \big(0.70 \times p + 0.15 \times \text{Strain}_{\text{hours}} + 0.15 \times \text{Strain}_{\text{budget}}\big)\Big)$$

### Risk Governance Tiers
- **$0–30$**: `LOW` (Healthy project within operational variance)
- **$31–60$**: `MEDIUM` (Emerging schedule or workload strain detected)
- **$61–100$**: `HIGH` (Critical delay probability requiring immediate rebalancing)

### Expected Delay Slippage (Calendar Days)
$$\text{Burn Multiplier} = \min\left(2.5, \; \max\left(1.0, \; \frac{actual\_hours}{\max(1.0, estimated\_hours \times (1 - \text{Remaining Ratio}))}\right)\right)$$
$$\text{Expected Delay} = \begin{cases} 
0.0 & \text{if } p < 0.25 \\
\text{round}\left(p \times \big(\text{Burn Multiplier} \times 14.0 + previous\_delays \times 2.0\big), 1\right) & \text{if } p \ge 0.25 
\end{cases}$$

---

## 11. Reusable Prediction Function
Implemented in `data-science/src/predict.py`:
```python
from predict import predict_project_risk

project_input = {
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

result = predict_project_risk(project_input)
# Result:
# {
#   "delay_probability": 0.01,
#   "risk_score": 1,
#   "risk_level": "LOW",
#   "expected_delay_days": 0.0
# }
```

---

## 12. Validated Test Scenarios

### Scenario 1: Low-Risk Project
- **Input:** 87.5% completed, 28h workload, 45 days runway, 0 past delays, ₹11L/₹15L budget.
- **Output:** `delay_probability = 0.01`, `risk_score = 1`, `risk_level = LOW`, `expected_delay_days = 0.0`

### Scenario 2: Medium-Risk Project
- **Input:** 48% completed, 40h workload, 28 days runway, 1 past delay, ₹10.5L/₹18L budget.
- **Output:** `delay_probability = 0.54`, `risk_score = 39`, `risk_level = MEDIUM`, `expected_delay_days = 9.5`

### Scenario 3: High-Risk Project
- **Input:** 21.8% completed, 56h workload, 8 days runway, 4 past delays, ₹15.5L/₹16L budget.
- **Output:** `delay_probability = 0.92`, `risk_score = 76`, `risk_level = HIGH`, `expected_delay_days = 39.6`

---

## 13. Limitations & Assumptions
1. **Point-in-Time Snapshot:** The model operates on a static cross-sectional project state rather than continuous recurrent sequential time series (e.g. LSTM/GRU).
2. **Fixed Scope Assumption:** The prediction evaluates currently recorded task totals and does not dynamically anticipate unlogged future scope creep.
3. **Simulated Baseline:** Trained on synthetic telemetry structured according to empirical software engineering dynamics.

---

## 14. Retraining & Reproducibility
To retrain the model and regenerate all results from scratch:
```bash
# 1. Regenerate raw dataset
python data-science/dataset/generate_data.py

# 2. Execute end-to-end training pipeline
python data-science/src/train_model.py

# 3. Run validation test suite
pytest data-science/test_ml.py -v
```
All random seeds are locked to `42` to guarantee exact mathematical reproducibility.
