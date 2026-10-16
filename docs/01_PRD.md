# ProjectPulse — Product Requirements Document (PRD)

**Tagline:** Track. Analyze. Predict. Deliver.  
**Domain:** Data Science + Project Management  
**Project Classification:** Internship MVP (Focused, Production-Ready, Non-Over-Engineered)  
**Document Version:** 1.0.0  
**Status:** Approved for Implementation  

---

## 1. Executive Summary

ProjectPulse is an intelligent, full-stack project management, data analytics, and risk prediction platform designed to solve one of the most persistent failure modes in software engineering and operations: unexpected schedule slippage and resource bottlenecks. 

While legacy project management tools function primarily as static record-keeping dashboards, ProjectPulse introduces an active, explainable Machine Learning (ML) layer built on a Random Forest Classifier. The platform tracks project workflows, task lifecycles, team workloads, deadlines, and financial budgets, while concurrently calculating real-time progress metrics and forecasting project delay probabilities. With delay probability, numerical risk scores (0–100), risk classifications (Low, Medium, High), and estimated delay days, ProjectPulse generates actionable, rule-grounded AI recommendations that empower project managers to reallocate resources and mitigate risks before deadlines are breached.

---

## 2. Problem Statement

Modern software teams operate in dynamic environments where scope expansion, uneven workload distribution, and task interdependencies frequently derail timelines. Key industry challenges include:

1. **Retrospective Rather than Predictive Management:** Existing tools (e.g., Trello, Jira) report what *has already occurred* (completed tasks, elapsed time), offering no empirical forecast of whether an in-flight project will meet its target delivery date.
2. **Hidden Bottlenecks and Workload Blindspots:** Managers struggle to visualize real-time correlations between individual team member overload, task complexity, and deadline velocity.
3. **Black-Box or Non-Existent Risk Scoring:** Small-to-medium teams lack accessible, explainable data science tooling to evaluate schedule health without complex enterprise BI overhead.
4. **Action Paralysis:** Raw statistics do not provide prescriptive remedies. Project managers need clear, deterministic recommendations (e.g., reassigning tasks, curbing scope) tailored to current risk indicators.

---

## 3. Proposed Solution

ProjectPulse bridges project execution and predictive data science in a lightweight, focused Minimum Viable Product (MVP):

- **Core Project Management Engine:** Provides structured project creation, milestone scheduling, task assignment, priority tagging, and estimated versus actual hours logging.
- **Real-Time Data Analytics Engine:** Automatically aggregates project completion rates, team workload balances, budget burn ratios, and productivity trajectories into visual dashboard metrics.
- **Explainable Machine Learning Engine:** Employs a trained Random Forest model that consumes project and task-level operational features (team size, task count, pending backlog, workload variance, hour deviations, deadline runway) to infer delay probabilities and risk scores.
- **Prescriptive AI Recommendations:** Evaluates ML predictions and operational threshold triggers to synthesize targeted mitigations: task redistribution, critical path prioritization, workload reduction, deadline monitoring, and budget reconciliation.

```
+-----------------------------------------------------------------------+
|                             ProjectPulse                              |
|                                                                       |
|   [Track]                  [Analyze]                [Predict & Deliver]|
|   Projects & Tasks   -->   Completion & Hours  -->  Random Forest ML   |
|   Milestones & Team        Budget & Workload        Risk Scores & Recs |
+-----------------------------------------------------------------------+
```

---

## 4. Target Users

| User Persona | Role | Primary Goals & Needs |
| :--- | :--- | :--- |
| **Project Manager (PM) / Scrum Lead** | Primary System Operator | Needs a central hub to create projects, configure milestones, monitor budget burn, inspect predictive risk alerts, and execute AI-guided workload rebalancing. |
| **Team Member / Software Engineer** | Operational Contributor | Needs a clutter-free view of assigned tasks, priority levels, estimated hours, and a direct mechanism to update task status and log actual work hours. |
| **Stakeholder / Academic Evaluator** | Observer / Reviewer | Evaluates project health trends, analytics accuracy, and inspects the validity and explainability of the underlying Data Science methodology. |

---

## 5. Goals and Objectives

### 5.1 Project Goals
- Deliver an achievable, high-quality, end-to-end software engineering and data science project suitable for an academic internship submission.
- Ensure all components—database schema, backend APIs, frontend interfaces, and ML pipelines—are cleanly integrated, performant, and fully explainable.
- Avoid architectural over-engineering while enforcing strict industry design standards (RESTful APIs, normalized database design, modular ML inference).

### 5.2 Measurable Objectives (MVP Key Results)
- **Sub-200ms ML Prediction Latency:** The risk prediction endpoint must execute feature ingestion, preprocessing, and Random Forest inference in under 200 milliseconds.
- **Zero-Ambiguity Risk Quantification:** Every active project must display an exact Delay Probability (0.00–1.00), Risk Score (0–100), Risk Category (Low, Medium, High), and Estimated Delay (days).
- **100% Traceable AI Recommendations:** All generated recommendations must directly map to explainable heuristics derived from prediction metrics and operational thresholds.
- **Full Operational Coverage:** Seamlessly handle CRUD operations for Projects, Tasks, Team Members, and Milestones without external third-party enterprise dependencies.

---

## 6. MVP Scope

The scope of ProjectPulse is deliberately bounded to maintain high craft, stability, and depth without excessive breadth.

### 6.1 Included In Scope (MVP Core)

#### A. Project Management
- **Project Lifecycle:** Creation, editing, status tracking (`Planning`, `In Progress`, `Completed`, `On Hold`), budget allocation, and target deadline definition.
- **Milestone Tracking:** Milestone title, target due date, status, and project association.
- **Task Management:** Title, description, project mapping, assigned team member, priority (`Low`, `Medium`, `High`, `Critical`), task status (`To Do`, `In Progress`, `Completed`), complexity rating (`1 - Low`, `2 - Medium`, `3 - High`), estimated hours, actual hours logged, and dependency indicator.
- **Team Workload:** Team member directory with assigned role, maximum weekly capacity, and live aggregate assigned hours.

#### B. Data Analytics
- Project completion percentage (`Completed Tasks / Total Tasks * 100`).
- Task velocity and completion rate.
- Team member workload distribution (assigned hours vs. capacity).
- Budget utilization ratio (`Actual Budget Spent / Total Budget Allocated`).
- Estimated vs. actual hours variance.
- Project Health Index (composite heuristic score based on time and budget burn).
- Productivity trends (completed vs. planned tasks across time).

#### C. Machine Learning & Predictive Analytics
- **Supervised Model:** Random Forest Classifier trained on structured project telemetry.
- **Outputs:**
  - Delay Probability ($P(\text{delay}) \in [0.0, 1.0]$).
  - Risk Score ($0 \text{ to } 100$).
  - Risk Level classification: `Low` ($0 - 39$), `Medium` ($40 - 69$), `High` ($70 - 100$).
  - Expected Delay in days.
- **Input Feature Set:** Team size, total tasks, completed tasks, pending tasks, average workload, estimated hours, actual hours, deadline days remaining, previous project delays, budget utilization, task complexity average, and blocking task dependencies.

#### D. AI Recommendations
Rule-guided heuristic engine fueled by ML outputs and project analytics:
1. *Redistribute Tasks:* Triggered when workload variance across members exceeds tolerance.
2. *Prioritize Critical Tasks:* Triggered when pending critical/high-complexity tasks jeopardize upcoming deadlines.
3. *Reduce Team Workload:* Triggered when actual hours logged exceed estimates by $\ge 20\%$ or average workload exceeds team capacity.
4. *Monitor Deadline:* Triggered when risk probability $\ge 0.60$ and deadline days remaining $\le 14$.
5. *Review Budget Usage:* Triggered when budget utilization exceeds percentage of project completion by $\ge 15\%$.

---

## 7. Out-of-Scope Features (Deferred Beyond MVP)

To safeguard engineering velocity and prevent scope creep, the following features are strictly deferred:
- Real-time instant messaging / chat channels between team members.
- Native two-way synchronization with external issue trackers (Jira, GitHub Issues, Asana).
- Multi-tenant enterprise SSO (SAML, Okta, Active Directory).
- Multi-currency payment processing and invoicing integrations.
- Native mobile applications (iOS/Android) — responsive web browser access only.
- Complex multi-dependency interactive Gantt chart drag-and-drop engines.
- Generative AI / Large Language Model (LLM) agent integrations (the ML core is purely statistical and explainable Data Science).

---

## 8. User Journeys

### Journey 1: Project Manager Monitoring Project Health & Acting on Risk
```
[Login / Auth]
      │
      ▼
[Executive Dashboard]  ──> Observes overall project portfolio health & alerts
      │
      ▼
[Project Details Screen]
      │
      ├──> Views completion (45%), hours logged (120/100 hrs), budget spend (85%)
      ├──> Triggers "Evaluate Risk" (Calls /api/predict-risk)
      │
      ▼
[AI Insights Panel]
      │
      ├──> ML Output: Risk Score = 78 (High), Delay Probability = 0.82, Exp. Delay = 9 Days
      └──> Recommendations Generated:
           • "Redistribute tasks: Developer Bob is at 140% capacity."
           • "Prioritize critical tasks: 3 high-complexity tasks remain unassigned."
      │
      ▼
[Tasks View] ──> PM reassigns overloaded tasks to Alice and updates deadlines.
```

### Journey 2: Developer Logging Task Progress
```
[Login / Auth]
      │
      ▼
[Tasks Screen] ──> Filters by "My Assigned Tasks"
      │
      ├──> Selects "Build Authentication Middleware"
      ├──> Changes Status from "In Progress" to "Completed"
      ├──> Updates Actual Hours from 6 to 8 hours
      │
      ▼
[System Updates]
      │
      └──> Project completion %, member workload, and hours variance automatically re-calculate.
```

---

## 9. Success Metrics

| Dimension | Metric | Target Threshold |
| :--- | :--- | :--- |
| **System Performance** | Backend REST API latency ($p95$) | $< 150 \text{ ms}$ |
| **ML Inference Speed** | Delay risk inference response time | $< 200 \text{ ms}$ |
| **Data Integrity** | Cascade integrity across Projects, Tasks, Milestones | $100\%$ schema enforced |
| **Predictive Reliability** | Model validation accuracy & F1-score | Evaluated via standard k-fold CV on dataset |
| **Recommendation Actionability** | Heuristic rules triggered appropriately per condition | $100\%$ deterministic rule adherence |
| **Usability & UX** | Responsive layout compatibility | Complete coverage across Desktop (1440px), Laptop (1024px), Tablet (768px) |

---

## 10. Future Scope (Post-MVP Roadmap)

1. **Model Iteration:** Benchmark Gradient Boosting (XGBoost/LightGBM) against the baseline Random Forest Classifier.
2. **Automated Sprint Retrospectives:** Auto-generation of sprint burndown velocity summaries.
3. **Notification Webhooks:** Outbound webhook alerts (Slack, Discord, Email) when a project transitions into the `High Risk` category.
4. **Historical Delay Tracking:** Automatic logging of completed project snapshots into the training pipeline to allow continuous active learning.
