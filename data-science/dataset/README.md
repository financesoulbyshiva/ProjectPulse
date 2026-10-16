# ProjectPulse — Dataset Documentation

## Overview
This directory contains the operational project snapshot dataset utilized to train, validate, and evaluate the ProjectPulse Machine Learning delay prediction pipeline.

> [!IMPORTANT]
> **Simulated Data Notice:** This dataset is simulated for the ProjectPulse internship prototype and is not presented as real organizational project data. It follows empirical distributions and dynamics observed in modern agile software engineering environments.

---

## Dataset Profile
- **File Name:** `project_data.csv`
- **Total Records:** 422 raw observation records (420 unique project snapshots)
- **Primary Target:** `delay_status` (`0` = On Time, `1` = Delayed)
- **Target Balance:** ~58.5% On Time (`0`), ~41.5% Delayed (`1`)

---

## Feature Dictionary

| Column Name | Data Type | Permissible Range | Unit / Scale | Description |
| :--- | :--- | :--- | :--- | :--- |
| `project_id` | String | PRJ-1001 to PRJ-1420 | Identifier | Unique project snapshot tracking code |
| `team_size` | Integer | [2, 16] | Contributors | Number of assigned engineers/designers |
| `total_tasks` | Integer | [15, 85] | Task Count | Total scope of work items |
| `completed_tasks` | Integer | [0, `total_tasks`] | Task Count | Completed tasks |
| `pending_tasks` | Integer | [0, `total_tasks`] | Task Count | Remaining backlog and in-progress tasks |
| `avg_workload` | Float | [15.0, 68.0] | Hours/Week/Dev | Average assigned weekly workload per contributor |
| `estimated_hours` | Float | [250.0, 2700.0] | Hours | Total planned engineering hours |
| `actual_hours` | Float | [0.0, 3200.0] | Hours | Cumulative hours logged to date |
| `deadline_days_remaining`| Integer | [2, 90] | Calendar Days | Runway days remaining until target delivery date |
| `previous_delays` | Integer | [0, 8] | Incident Count| Historical milestone slippages or past late deliverables |
| `budget` | Float | [₹1,00,000, ₹25,00,000] | INR (₹) | Total approved financial project budget |
| `spent_budget` | Float | [₹0, ₹27,00,000] | INR (₹) | Cumulative project expenditure to date |
| `task_complexity` | Float | [1.0, 3.0] | Score | Mean complexity rating (1.0 = Low, 2.0 = Medium, 3.0 = High) |
| `dependencies` | Integer | [0, 25] | Task Count | Count of tasks blocked by or dependent on external items |
| `delay_status` | Integer | {0, 1} | Binary Label | Target label (0 = Delivered On Time, 1 = Missed Deadline) |

---

## Generation & Reproduction
The dataset can be deterministically reproduced at any time using:
```bash
python data-science/dataset/generate_data.py
```
Random seed is locked to `42` to guarantee exact scientific reproducibility.
