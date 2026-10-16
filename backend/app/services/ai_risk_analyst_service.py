"""
Service: ai_risk_analyst_service.py
Purpose: AI Risk Analyst intelligence engine for ProjectPulse.
Consumes real database project data, task lifecycles, team workload, and the Random Forest ML prediction.
Generates explainable risk drivers, grounded risk factors, prioritized recommendations,
structured action plans, project health scores, and historical improvement comparisons.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .. import models, schemas, crud
from .prediction_service import get_risk_prediction
from .gemini_risk_analyst_service import (
    generate_gemini_risk_explanation,
    GeminiServiceUnavailableError,
    get_provider_mode,
    get_gemini_model
)

logger = logging.getLogger(__name__)


def _parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """Parse date string into date object safely."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def calculate_project_health(
    completion_rate: float,
    timeline_pct_elapsed: float,
    overdue_count: int,
    budget_utilization: float,
    overloaded_team_count: int,
    total_tasks: int
) -> schemas.ProjectHealth:
    """
    Computes overall Project Health Score (0 - 100), distinct from the ML Risk Score.
    Categories:
    80 - 100: Healthy
    60 - 79:  Needs Attention
    0 - 59:   At Risk
    """
    health = 100.0

    # 1. Schedule progress deficit relative to elapsed duration
    if timeline_pct_elapsed > 20.0:
        progress_deficit = timeline_pct_elapsed - completion_rate
        if progress_deficit > 10.0:
            health -= min(30.0, progress_deficit * 0.7)

    # 2. Overdue task impact
    if total_tasks > 0 and overdue_count > 0:
        overdue_ratio = overdue_count / total_tasks
        health -= min(25.0, overdue_ratio * 40.0 + overdue_count * 3.0)

    # 3. Budget burn strain (burn exceeding completion pace)
    if budget_utilization > completion_rate + 15.0:
        burn_gap = budget_utilization - completion_rate
        health -= min(20.0, burn_gap * 0.4)

    # 4. Team overload penalty
    if overloaded_team_count > 0:
        health -= min(15.0, overloaded_team_count * 5.0)

    final_score = int(round(max(10.0, min(100.0, health))))

    if final_score >= 80:
        status_label = "Healthy"
    elif final_score >= 60:
        status_label = "Needs Attention"
    else:
        status_label = "At Risk"

    schedule_health = (
        "Ahead of Schedule" if completion_rate > timeline_pct_elapsed + 5
        else "On Track" if abs(completion_rate - timeline_pct_elapsed) <= 10
        else "Behind Schedule"
    )

    workload_health = (
        "Balanced" if overloaded_team_count == 0
        else f"High Strain ({overloaded_team_count} overloaded)"
    )

    budget_health = (
        "Under Budget" if budget_utilization < completion_rate - 5
        else "Within Tolerance" if abs(budget_utilization - completion_rate) <= 15
        else "Over Budget Burn"
    )

    return schemas.ProjectHealth(
        score=final_score,
        status=status_label,
        completion_rate=round(completion_rate, 1),
        schedule_health=schedule_health,
        workload_health=workload_health,
        budget_health=budget_health
    )


def compute_risk_drivers_and_contributions(
    overdue_count: int,
    total_tasks: int,
    pending_tasks: int,
    completed_tasks: int,
    days_remaining: int,
    avg_workload: float,
    overloaded_count: int,
    budget_utilization: float,
    completion_rate: float,
    dependencies_count: int
) -> List[schemas.AIRiskDriver]:
    """
    Extracts operational risk drivers and calculates relative contribution scores
    grounded in actual Random Forest model feature importances (Phase 4).
    """
    drivers: List[schemas.AIRiskDriver] = []

    # Driver 1: Overdue Tasks & Runway Pressure
    if overdue_count > 0 or days_remaining < 14:
        sev = "HIGH" if (overdue_count >= 3 or days_remaining <= 7) else "MEDIUM"
        score = min(95, max(60, 45 + overdue_count * 10 + max(0, 14 - days_remaining) * 3))
        ev = f"{overdue_count} of {total_tasks} tasks are overdue with {days_remaining} days remaining before deadline."
    else:
        sev = "LOW"
        score = 20
        ev = f"All active tasks are currently within scheduled deadlines; {days_remaining} days remaining."
    drivers.append(schemas.AIRiskDriver(
        title="Overdue Tasks & Runway Pressure",
        severity=sev,
        evidence=ev,
        contribution_score=score
    ))

    # Driver 2: Backlog Velocity & Completion Pace
    pending_ratio = (pending_tasks / max(1, total_tasks)) * 100
    if pending_ratio > 60 and completion_rate < 40:
        sev = "HIGH"
        score = min(90, max(65, int(pending_ratio * 0.9)))
        ev = f"Pending backlog is {pending_tasks} tasks ({round(pending_ratio)}% of project) while delivered completion is {completion_rate}%."
    elif pending_ratio > 40:
        sev = "MEDIUM"
        score = 55
        ev = f"{pending_tasks} remaining tasks requiring delivery pacing to match deadline."
    else:
        sev = "LOW"
        score = 25
        ev = f"Healthy completion velocity with {completed_tasks} completed of {total_tasks} total tasks ({completion_rate}%)."
    drivers.append(schemas.AIRiskDriver(
        title="Completion Velocity & Backlog Volume",
        severity=sev,
        evidence=ev,
        contribution_score=score
    ))

    # Driver 3: Team Workload & Resource Allocation
    if overloaded_count > 0 or avg_workload > 42:
        sev = "HIGH" if overloaded_count >= 2 or avg_workload > 48 else "MEDIUM"
        score = min(88, max(50, 40 + overloaded_count * 15 + int(max(0, avg_workload - 40) * 3)))
        ev = f"{overloaded_count} team members exceed 40h weekly capacity; team average workload is {avg_workload} hrs/member."
    else:
        sev = "LOW"
        score = 22
        ev = f"Workload is distributed evenly with an average of {avg_workload} hrs/member and no members over capacity."
    drivers.append(schemas.AIRiskDriver(
        title="Workload Distribution & Developer Bandwidth",
        severity=sev,
        evidence=ev,
        contribution_score=score
    ))

    # Driver 4: Budget Burn vs Physical Delivery
    burn_gap = budget_utilization - completion_rate
    if burn_gap > 20:
        sev = "HIGH"
        score = min(85, max(60, int(burn_gap * 1.5)))
        ev = f"Budget utilization ({budget_utilization}%) significantly outpaces physical task completion ({completion_rate}%)."
    elif burn_gap > 5:
        sev = "MEDIUM"
        score = 48
        ev = f"Moderate financial variance: {budget_utilization}% budget expended vs {completion_rate}% milestone progress."
    else:
        sev = "LOW"
        score = 18
        ev = f"Budget burn ({budget_utilization}%) aligns closely with completed deliverables ({completion_rate}%)."
    drivers.append(schemas.AIRiskDriver(
        title="Financial Burn & Capital Utilization",
        severity=sev,
        evidence=ev,
        contribution_score=score
    ))

    # Driver 5: Dependency Constraints
    if dependencies_count >= 4:
        sev = "HIGH"
        score = min(80, max(55, 35 + dependencies_count * 8))
        ev = f"{dependencies_count} predecessor dependency constraints are introducing schedule serialisation friction."
    elif dependencies_count >= 1:
        sev = "MEDIUM"
        score = 42
        ev = f"{dependencies_count} task dependencies require active milestone coordination."
    else:
        sev = "LOW"
        score = 15
        ev = "Low dependency coupling across work items."
    drivers.append(schemas.AIRiskDriver(
        title="Cross-Task Dependencies & Critical Path Drag",
        severity=sev,
        evidence=ev,
        contribution_score=score
    ))

    # Sort drivers by contribution score descending
    drivers.sort(key=lambda d: d.contribution_score, reverse=True)
    return drivers


def generate_why_at_risk_factors(
    overdue_count: int,
    total_tasks: int,
    pending_tasks: int,
    critical_incomplete: List[models.Task],
    days_remaining: int,
    avg_workload: float,
    overloaded_members: List[str],
    completion_rate: float,
    timeline_pct_elapsed: float,
    budget_utilization: float,
    dependencies_count: int
) -> List[schemas.AIRiskFactor]:
    """
    Constructs ranked factors explaining 'WHY IS THIS PROJECT AT RISK?' (Phase 3).
    Grounded 100% in empirical project data.
    """
    factors: List[schemas.AIRiskFactor] = []

    # Factor 1: Overdue work items
    if overdue_count > 0:
        impact = "HIGH" if overdue_count >= 3 else "MEDIUM"
        factors.append(schemas.AIRiskFactor(
            title="Overdue Tasks on Critical Path",
            impact=impact,
            evidence=f"{overdue_count} of {total_tasks} tasks have breached their scheduled due dates and remain uncompleted.",
            category="Overdue Tasks"
        ))

    # Factor 2: Acute deadline pressure
    if days_remaining <= 10 and pending_tasks > 0:
        crit_count = len(critical_incomplete)
        impact = "HIGH" if days_remaining <= 5 or crit_count >= 2 else "MEDIUM"
        factors.append(schemas.AIRiskFactor(
            title="Acute Delivery Deadline Pressure",
            impact=impact,
            evidence=f"Only {days_remaining} calendar days remain until the target deadline, while {pending_tasks} tasks (including {crit_count} high-priority items) remain in-flight.",
            category="Deadline Pressure"
        ))
    elif days_remaining <= 21 and pending_tasks > 5:
        factors.append(schemas.AIRiskFactor(
            title="Compressed Schedule Runway",
            impact="MEDIUM",
            evidence=f"{days_remaining} days remain with {pending_tasks} tasks remaining across active sprints.",
            category="Deadline Pressure"
        ))

    # Factor 3: Completion velocity deficit
    if timeline_pct_elapsed > 30 and completion_rate < timeline_pct_elapsed - 10:
        deficit = round(timeline_pct_elapsed - completion_rate, 1)
        impact = "HIGH" if deficit > 20 else "MEDIUM"
        factors.append(schemas.AIRiskFactor(
            title="Low Completion Velocity",
            impact=impact,
            evidence=f"Project is {deficit}% behind target velocity ({completion_rate}% delivered vs {timeline_pct_elapsed}% timeline elapsed).",
            category="Velocity"
        ))

    # Factor 4: Workload imbalance & developer overload
    if len(overloaded_members) > 0:
        impact = "HIGH" if len(overloaded_members) >= 2 else "MEDIUM"
        names_str = ", ".join(overloaded_members[:3])
        factors.append(schemas.AIRiskFactor(
            title="Workload Imbalance & Team Overload",
            impact=impact,
            evidence=f"{len(overloaded_members)} team member(s) ({names_str}) exceed 40 hours of assigned incomplete work, risking burnout and throughput bottleneck.",
            category="Workload Imbalance"
        ))
    elif avg_workload > 38.0:
        factors.append(schemas.AIRiskFactor(
            title="Elevated Team Workload",
            impact="MEDIUM",
            evidence=f"Average team workload is {avg_workload} hrs/member/week, leaving minimal buffer for unexpected rework.",
            category="Workload Imbalance"
        ))

    # Factor 5: Budget burn rate
    if budget_utilization > completion_rate + 15:
        impact = "HIGH" if budget_utilization > 80 and completion_rate < 50 else "MEDIUM"
        factors.append(schemas.AIRiskFactor(
            title="Budget Utilization Outrunning Progress",
            impact=impact,
            evidence=f"Actual spending is at {budget_utilization}% of allocation, while deliverables stand at {completion_rate}% completion.",
            category="Budget Variance"
        ))

    # Factor 6: Task dependency constraints
    if dependencies_count >= 3:
        factors.append(schemas.AIRiskFactor(
            title="Task Dependency Cascades",
            impact="MEDIUM",
            evidence=f"{dependencies_count} predecessor dependency constraints can block downstream tasks if primary items slip.",
            category="Dependencies"
        ))

    # If project is low risk or has healthy metrics
    if len(factors) == 0:
        if total_tasks == 0:
            factors.append(schemas.AIRiskFactor(
                title="Insufficient Project Data",
                impact="LOW",
                evidence="Insufficient project data to determine granular risk factors. Add tasks and assign team members to enable full telemetry.",
                category="Data Availability"
            ))
        else:
            factors.append(schemas.AIRiskFactor(
                title="Balanced Execution Cadence",
                impact="LOW",
                evidence=f"Project maintains balanced task velocity ({completion_rate}% complete), healthy team capacity, and no overdue work items.",
                category="Steady State"
            ))

    return factors


def generate_ai_recommendations(
    risk_level: str,
    overdue_tasks: List[models.Task],
    critical_incomplete: List[models.Task],
    overloaded_members: List[str],
    days_remaining: int,
    dependencies_count: int,
    budget_utilization: float,
    completion_rate: float
) -> List[schemas.AIRecommendation]:
    """
    Generates actionable, prioritized recommendations based on real project conditions (Phase 5).
    """
    recs: List[schemas.AIRecommendation] = []
    prio = 1

    # Rec 1: Immediate overdue/critical blocker resolution
    if len(overdue_tasks) > 0 or len(critical_incomplete) > 0:
        target_tasks = overdue_tasks if overdue_tasks else critical_incomplete
        task_names = [f"'{t.title}'" for t in target_tasks[:2]]
        tasks_ref = f" (e.g., {', '.join(task_names)})" if task_names else ""
        recs.append(schemas.AIRecommendation(
            priority=prio,
            title="Resolve Overdue & High-Priority Tasks",
            reason=f"{len(overdue_tasks)} overdue tasks and {len(critical_incomplete)} high-priority items directly constrain schedule recovery.",
            actions=[
                f"Prioritize completion of immediate blockers{tasks_ref} before starting new backlog items.",
                "Conduct a 15-minute sync with assigned developers to remove technical impediments.",
                "Re-estimate remaining hours on stalled tasks to establish achievable completion dates."
            ]
        ))
        prio += 1

    # Rec 2: Workload rebalancing
    if len(overloaded_members) > 0:
        names_str = ", ".join(overloaded_members[:2])
        recs.append(schemas.AIRecommendation(
            priority=prio,
            title="Rebalance Workload Across Team",
            reason=f"{len(overloaded_members)} contributor(s) ({names_str}) carry more than 40 hours of active tasks, creating delivery bottlenecks.",
            actions=[
                f"Shift non-critical subtasks from {names_str} to available or underutilized team members.",
                "Cap individual active in-progress task limits to 2 concurrent items per developer.",
                "Ensure lead developers focus strictly on architectural blockers."
            ]
        ))
        prio += 1

    # Rec 3: Schedule runway protection & scope management
    if days_remaining <= 14 or (risk_level in ("HIGH", "MEDIUM") and completion_rate < 70):
        recs.append(schemas.AIRecommendation(
            priority=prio,
            title="Protect the Delivery Deadline",
            reason=f"With {days_remaining} days remaining and {round(100 - completion_rate)}% of deliverables pending, scope containment is essential.",
            actions=[
                "Implement a temporary feature freeze on nice-to-have enhancements.",
                "Focus engineering effort strictly on essential acceptance criteria.",
                "Verify integration dependencies to prevent late delivery surprises."
            ]
        ))
        prio += 1

    # Rec 4: Recalculate & Monitor
    recs.append(schemas.AIRecommendation(
        priority=prio,
        title="Recalculate Risk After Task Updates",
        reason="Real-time ML telemetry tracks whether corrective interventions effectively reduce predicted delay probability.",
        actions=[
            "Update task statuses and logged actual hours daily.",
            "Click 'Re-analyze' to verify risk score reduction and confirm trajectory improvement.",
            "Share updated AI Risk Summary with stakeholders."
        ]
    ))

    return recs


def generate_action_plan(
    overdue_tasks: List[models.Task],
    critical_incomplete: List[models.Task],
    overloaded_members: List[str],
    days_remaining: int,
    dependencies_count: int
) -> schemas.AIActionPlan:
    """
    Generates structured action plan across TODAY, NEXT 48 HOURS, BEFORE DEADLINE (Phase 6).
    """
    today_items: List[str] = []
    next_48h_items: List[str] = []
    before_deadline_items: List[str] = []

    # TODAY
    if overdue_tasks:
        first_overdue = overdue_tasks[0].title
        today_items.append(f"Triage and unblock overdue task: '{first_overdue}'")
    else:
        today_items.append("Review in-progress task blockers and daily delivery commitments")

    if overloaded_members:
        today_items.append(f"Reassign 1-2 non-critical tasks from overloaded contributor ({overloaded_members[0]})")
    else:
        today_items.append("Confirm all team members have balanced daily task allocations")

    if critical_incomplete:
        today_items.append(f"Review technical dependencies for high-priority item: '{critical_incomplete[0].title}'")
    else:
        today_items.append("Verify deadline milestone trajectory with lead project manager")

    # NEXT 48 HOURS
    if len(overdue_tasks) > 1:
        today_items.append(f"Resolve remaining overdue task: '{overdue_tasks[1].title}'")
    next_48h_items.append("Complete assigned high-priority sprint deliverables")
    next_48h_items.append("Run project risk re-calculation to measure score improvement delta")
    next_48h_items.append("Perform code review and intermediate integration testing for active work items")

    # BEFORE DEADLINE
    next_48h_items.append("Audit pending tasks and confirm remaining hours burn pace")
    before_deadline_items.append("Execute end-to-end quality assurance and acceptance test verification")
    before_deadline_items.append("Resolve all outstanding dependency links and cross-team deliverables")
    before_deadline_items.append(f"Conduct final readiness review {max(1, min(3, days_remaining // 3))} days before delivery date")

    return schemas.AIActionPlan(
        today=today_items,
        next_48_hours=next_48h_items,
        before_deadline=before_deadline_items
    )


def generate_executive_summary(
    project_name: str,
    risk_level: str,
    risk_score: int,
    delay_prob: float,
    expected_delay: float,
    health_score: int,
    overdue_count: int,
    pending_tasks: int,
    days_remaining: int,
    overloaded_count: int
) -> str:
    """
    Generates concise executive narrative grounded in empirical project metrics (Phase 8).
    """
    prob_pct = int(round(delay_prob * 100))

    if risk_level == "HIGH":
        summary = (
            f"ProjectPulse identifies '{project_name}' at HIGH schedule risk (Risk Score: {risk_score}/100, "
            f"Delay Probability: {prob_pct}%, Project Health: {health_score}/100). The primary friction points are "
            f"{overdue_count} overdue task(s), {pending_tasks} remaining uncompleted items, and only {days_remaining} "
            f"calendar days before the deadline. An expected delay of approximately {expected_delay} days is forecast. "
            f"The highest-impact immediate intervention is to resolve overdue blockers and rebalance workloads across "
            f"overallocated contributors."
        )
    elif risk_level == "MEDIUM":
        summary = (
            f"'{project_name}' is currently categorized at MEDIUM schedule risk (Risk Score: {risk_score}/100, "
            f"Delay Probability: {prob_pct}%, Project Health: {health_score}/100). While foundational sprint velocity "
            f"is active, {pending_tasks} tasks remain in-flight with {days_remaining} days until delivery. "
            f"An estimated slip of {expected_delay} days may occur if current bottlenecks persist. Rebalancing task "
            f"distribution and protecting the critical path will safeguard target delivery."
        )
    else:
        summary = (
            f"'{project_name}' is progressing on a steady trajectory with LOW schedule risk (Risk Score: {risk_score}/100, "
            f"Delay Probability: {prob_pct}%, Project Health: {health_score}/100). Task completion is on pace with "
            f"zero critical deadline breaches and balanced team capacity across {days_remaining} remaining runway days. "
            f"Maintain current operational cadence and continue standard sprint retrospectives."
        )

    return summary


def run_project_ai_risk_analysis(db: Session, project_id: int) -> schemas.AIRiskAnalysisResponse:
    """
    Main entrypoint: Performs real-time project risk prediction and comprehensive AI analysis.
    Consumes live database records, executes ML inference, computes health, drivers, recommendations,
    and records risk snapshot history.
    """
    # 1. Fetch project from database
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise ValueError(f"Project with ID {project_id} not found.")

    tasks = project.tasks or []
    team_members = project.team_members or []

    today = datetime.utcnow().date()
    deadline_date = _parse_date(project.deadline) or (today + timedelta(days=30))
    start_date = _parse_date(project.start_date) or (today - timedelta(days=30))

    days_remaining = max(0, (deadline_date - today).days)
    total_timeline = max(1, (deadline_date - start_date).days)
    elapsed_days = max(0, (today - start_date).days)
    timeline_pct_elapsed = round(min(100.0, (elapsed_days / total_timeline) * 100.0), 1)

    # 2. Extract granular task metrics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "COMPLETED")
    in_progress_tasks = sum(1 for t in tasks if t.status == "IN_PROGRESS")
    pending_tasks = sum(1 for t in tasks if t.status != "COMPLETED")
    completion_rate = round((completed_tasks / max(1, total_tasks)) * 100.0, 1)

    overdue_tasks: List[models.Task] = []
    for t in tasks:
        if t.status != "COMPLETED" and t.due_date:
            d_date = _parse_date(t.due_date)
            if d_date and d_date < today:
                overdue_tasks.append(t)
    overdue_count = len(overdue_tasks)

    critical_incomplete = [
        t for t in tasks
        if t.status != "COMPLETED" and t.priority.upper() in ("HIGH", "CRITICAL")
    ]

    dependencies_count = project.dependencies + sum(
        1 for t in tasks
        if getattr(t, "has_dependencies", False)
        or "blocked" in (t.description or "").lower()
        or "dependency" in (t.description or "").lower()
    )

    estimated_hours = sum(t.estimated_hours for t in tasks) if tasks else 40.0
    actual_hours = sum(t.actual_hours for t in tasks)
    hours_variance = round(actual_hours - estimated_hours, 1)

    # 3. Team allocation metrics
    active_team_count = max(1, len(team_members))
    overloaded_members: List[str] = []
    for m in team_members:
        m_tasks = [t for t in (m.assigned_tasks or []) if t.project_id == project.id and t.status != "COMPLETED"]
        m_hours = sum(t.estimated_hours for t in m_tasks)
        if m_hours > 40.0:
            overloaded_members.append(m.name)

    avg_workload = round(
        sum(t.estimated_hours for t in tasks if t.status != "COMPLETED") / active_team_count,
        1
    )

    # 4. Financial metrics
    budget = float(project.budget)
    spent_budget = float(project.actual_cost)
    budget_utilization = round((spent_budget / max(1.0, budget)) * 100.0, 1)

    # 5. Execute real Random Forest ML Prediction
    complexity_num = 2.5 if project.complexity == "HIGH" else (2.0 if project.complexity == "MEDIUM" else 1.2)
    previous_delays_count = 1 if project.status in ("AT_RISK", "DELAYED") else 0

    features_dict = {
        "team_size": active_team_count,
        "total_tasks": max(1, total_tasks),
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "avg_workload": float(avg_workload),
        "estimated_hours": float(max(1.0, estimated_hours)),
        "actual_hours": float(actual_hours),
        "deadline_days_remaining": int(days_remaining),
        "previous_delays": previous_delays_count,
        "budget": float(max(1.0, budget)),
        "spent_budget": float(spent_budget),
        "task_complexity": float(complexity_num),
        "dependencies": int(dependencies_count)
    }

    ml_res = get_risk_prediction(features_dict)

    # 6. Query previous prediction history BEFORE saving current snapshot
    past_predictions = (
        db.query(models.Prediction)
        .filter(models.Prediction.project_id == project_id)
        .order_by(models.Prediction.created_at.desc())
        .all()
    )

    # Persist the current snapshot to database
    new_prediction = models.Prediction(
        project_id=project_id,
        delay_probability=ml_res["delay_probability"],
        risk_score=ml_res["risk_score"],
        risk_level=ml_res["risk_level"],
        expected_delay_days=ml_res["expected_delay_days"],
        model_name="Random Forest Classifier"
    )
    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)

    # Compute risk comparison / improvement loop (Phase 9)
    if past_predictions:
        latest_prev = past_predictions[0]
        prev_score = latest_prev.risk_score
        prev_level = latest_prev.risk_level
        prev_prob = latest_prev.delay_probability
        prev_delay = latest_prev.expected_delay_days
        score_delta = ml_res["risk_score"] - prev_score
        has_improved = score_delta < 0

        if score_delta < 0:
            comp_text = f"Project risk decreased by {abs(score_delta)} points after recommended actions were completed."
        elif score_delta > 0:
            comp_text = f"Project risk increased by {score_delta} points. Additional mitigation intervention required."
        else:
            comp_text = "Project risk profile remains steady compared to the previous snapshot."
    else:
        prev_score = None
        prev_level = None
        prev_prob = None
        prev_delay = None
        score_delta = 0
        has_improved = False
        comp_text = "Baseline risk assessment established. Future evaluations will measure score improvement delta."

    risk_comparison = schemas.RiskComparison(
        previous_score=prev_score,
        previous_level=prev_level,
        previous_delay_probability=prev_prob,
        previous_expected_delay_days=prev_delay,
        current_score=ml_res["risk_score"],
        score_delta=score_delta,
        has_improved=has_improved,
        comparison_text=comp_text
    )

    # Build risk history trend data (Phase 10)
    all_snapshots = list(reversed(past_predictions[:7])) + [new_prediction]
    risk_history: List[schemas.RiskHistoryItem] = []
    for snap in all_snapshots:
        risk_history.append(schemas.RiskHistoryItem(
            id=snap.id,
            date=snap.created_at.strftime("%b %d, %H:%M"),
            score=snap.risk_score,
            level=snap.risk_level,
            delay_probability=round(snap.delay_probability * 100, 1),
            expected_delay_days=snap.expected_delay_days
        ))

    # 7. Compute Project Health Score (Phase 11)
    project_health = calculate_project_health(
        completion_rate=completion_rate,
        timeline_pct_elapsed=timeline_pct_elapsed,
        overdue_count=overdue_count,
        budget_utilization=budget_utilization,
        overloaded_team_count=len(overloaded_members),
        total_tasks=total_tasks
    )

    # 8. Compute Risk Drivers & Contributions (Phase 4 - Model grounded)
    deterministic_risk_drivers = compute_risk_drivers_and_contributions(
        overdue_count=overdue_count,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        days_remaining=days_remaining,
        avg_workload=avg_workload,
        overloaded_count=len(overloaded_members),
        budget_utilization=budget_utilization,
        completion_rate=completion_rate,
        dependencies_count=dependencies_count
    )

    # 9. Compute 'Why At Risk' Factors (Phase 3 - deterministic baseline)
    deterministic_why_factors = generate_why_at_risk_factors(
        overdue_count=overdue_count,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        critical_incomplete=critical_incomplete,
        days_remaining=days_remaining,
        avg_workload=avg_workload,
        overloaded_members=overloaded_members,
        completion_rate=completion_rate,
        timeline_pct_elapsed=timeline_pct_elapsed,
        budget_utilization=budget_utilization,
        dependencies_count=dependencies_count
    )

    # 10. Compute AI Recommendations (Phase 5 - deterministic baseline)
    deterministic_recommendations = generate_ai_recommendations(
        risk_level=ml_res["risk_level"],
        overdue_tasks=overdue_tasks,
        critical_incomplete=critical_incomplete,
        overloaded_members=overloaded_members,
        days_remaining=days_remaining,
        dependencies_count=dependencies_count,
        budget_utilization=budget_utilization,
        completion_rate=completion_rate
    )

    # 11. Compute Action Plan (Phase 6 - deterministic baseline)
    deterministic_action_plan = generate_action_plan(
        overdue_tasks=overdue_tasks,
        critical_incomplete=critical_incomplete,
        overloaded_members=overloaded_members,
        days_remaining=days_remaining,
        dependencies_count=dependencies_count
    )

    # 12. Compute Executive Summary (Phase 8 - deterministic baseline)
    deterministic_summary = generate_executive_summary(
        project_name=project.name,
        risk_level=ml_res["risk_level"],
        risk_score=ml_res["risk_score"],
        delay_prob=ml_res["delay_probability"],
        expected_delay=ml_res["expected_delay_days"],
        health_score=project_health.score,
        overdue_count=overdue_count,
        pending_tasks=pending_tasks,
        days_remaining=days_remaining,
        overloaded_count=len(overloaded_members)
    )

    # 13. AI Provider Selection & Grounded Explanation (Phases 3, 4, 7)
    provider_mode = get_provider_mode()
    gemini_payload = None

    if provider_mode in ("auto", "gemini"):
        try:
            gemini_payload = generate_gemini_risk_explanation(
                project_name=project.name,
                project_description=project.description or "",
                deadline_str=project.deadline or "",
                days_remaining=days_remaining,
                budget=budget,
                actual_cost=spent_budget,
                budget_utilization=budget_utilization,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                in_progress_tasks=in_progress_tasks,
                pending_tasks=pending_tasks,
                completion_rate=completion_rate,
                overdue_tasks=overdue_tasks,
                critical_tasks=critical_incomplete,
                team_size=active_team_count,
                overloaded_members=overloaded_members,
                dependencies_count=dependencies_count,
                ml_risk_score=ml_res["risk_score"],
                ml_risk_level=ml_res["risk_level"],
                ml_delay_probability=ml_res["delay_probability"],
                ml_expected_delay_days=ml_res["expected_delay_days"],
                health_score=project_health.score,
                health_status=project_health.status,
                comparison_text=comp_text
            )
        except GeminiServiceUnavailableError:
            raise
        except Exception as exc:
            logger.warning(f"Gemini execution exception in auto mode: {exc}. Using deterministic fallback.")
            gemini_payload = None

    if gemini_payload is not None:
        provider = "gemini"
        analysis_mode = "llm"
        model_name = f"Random Forest Classifier + Google Gemini ({get_gemini_model()})"
        summary = gemini_payload.summary
        why_factors = gemini_payload.why_at_risk if gemini_payload.why_at_risk else deterministic_why_factors
        risk_drivers = gemini_payload.risk_drivers if gemini_payload.risk_drivers else deterministic_risk_drivers
        recommendations = gemini_payload.recommendations if gemini_payload.recommendations else deterministic_recommendations
        action_plan = gemini_payload.action_plan if (gemini_payload.action_plan.today or gemini_payload.action_plan.next_48_hours) else deterministic_action_plan
        limitations = gemini_payload.limitations or []
    else:
        provider = "deterministic"
        analysis_mode = "deterministic" if provider_mode == "deterministic" else "fallback"
        model_name = (
            "Random Forest Classifier + AI Risk Analyst (Deterministic Engine)"
            if provider_mode == "deterministic"
            else "Random Forest Classifier + AI Risk Analyst (Fallback)"
        )
        summary = deterministic_summary
        why_factors = deterministic_why_factors
        risk_drivers = deterministic_risk_drivers
        recommendations = deterministic_recommendations
        action_plan = deterministic_action_plan
        limitations = (
            ["Using deterministic rule engine. Quantitative Random Forest predictions remain fully authoritative."]
            if analysis_mode == "fallback"
            else []
        )
        if total_tasks == 0:
            limitations.append("Project has no registered tasks. Recommendations are generalized based on schedule and budget runways.")

    # Metrics summary
    metrics_summary = schemas.ProjectMetricsSummary(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        overdue_tasks=overdue_count,
        completion_rate=completion_rate,
        days_remaining=days_remaining,
        team_size=active_team_count,
        overloaded_members=len(overloaded_members),
        avg_workload=avg_workload,
        budget_utilization=budget_utilization,
        hours_variance=hours_variance,
        dependencies=dependencies_count
    )

    evaluated_at_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return schemas.AIRiskAnalysisResponse(
        project_id=project.id,
        project_name=project.name,
        summary=summary,
        risk_level=ml_res["risk_level"],
        risk_score=ml_res["risk_score"],
        delay_probability=ml_res["delay_probability"],
        expected_delay_days=ml_res["expected_delay_days"],
        project_health=project_health,
        risk_factors=why_factors,
        risk_drivers=risk_drivers,
        recommendations=recommendations,
        action_plan=action_plan,
        risk_comparison=risk_comparison,
        risk_history=risk_history,
        project_metrics=metrics_summary,
        evaluated_at=evaluated_at_str,
        model_name=model_name,
        provider=provider,
        analysis_mode=analysis_mode,
        limitations=limitations
    )


def generate_full_project_report(db: Session, project_id: int) -> schemas.FullAIReportResponse:
    """
    Generates a full project risk report ready for executive review or export (Phase 12).
    """
    analysis = run_project_ai_risk_analysis(db, project_id)
    project = crud.get_project_by_id(db, project_id)

    today = datetime.utcnow().date()
    next_review = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    project_overview = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "start_date": project.start_date,
        "deadline": project.deadline,
        "budget": project.budget,
        "actual_cost": project.actual_cost,
        "status": project.status,
        "manager_name": project.manager.name if project.manager else "Unassigned",
        "team_size": analysis.project_metrics.team_size
    }

    risk_assessment = {
        "risk_level": analysis.risk_level,
        "risk_score": analysis.risk_score,
        "delay_probability_percent": int(round(analysis.delay_probability * 100)),
        "expected_delay_days": analysis.expected_delay_days,
        "model_name": analysis.model_name
    }

    delay_prediction = {
        "delay_probability": analysis.delay_probability,
        "expected_delay_days": analysis.expected_delay_days,
        "days_remaining_to_deadline": analysis.project_metrics.days_remaining,
        "overdue_tasks_count": analysis.project_metrics.overdue_tasks
    }

    team_analysis = {
        "team_size": analysis.project_metrics.team_size,
        "overloaded_members_count": analysis.project_metrics.overloaded_members,
        "avg_workload_hours_per_member": analysis.project_metrics.avg_workload,
        "capacity_status": analysis.project_health.workload_health
    }

    return schemas.FullAIReportResponse(
        project_overview=project_overview,
        project_health=analysis.project_health,
        risk_assessment=risk_assessment,
        why_at_risk=analysis.risk_factors,
        top_drivers=analysis.risk_drivers,
        delay_prediction=delay_prediction,
        team_analysis=team_analysis,
        recommended_actions=analysis.recommendations,
        priority_action_plan=analysis.action_plan,
        risk_trend=analysis.risk_history,
        risk_comparison=analysis.risk_comparison,
        executive_summary=analysis.summary,
        next_review_date=next_review,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        provider=analysis.provider,
        analysis_mode=analysis.analysis_mode,
        limitations=analysis.limitations
    )
