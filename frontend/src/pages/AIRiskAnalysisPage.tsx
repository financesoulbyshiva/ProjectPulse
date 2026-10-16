import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  AlertTriangle,
  FileText,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Clock,
  Activity,
  Printer,
  Copy,
  Check,
} from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { RiskGauge } from '../components/charts/RiskGauge';
import { AnimatedNumber } from '../components/common/AnimatedNumber';
import { Modal } from '../components/common/Modal';
import { api } from '../services/api';
import type { AIRiskAnalysisResponse, FullAIReportResponse } from '../types';

const PIPELINE_SIGNALS = [
  { name: 'Timeline & Milestone Velocity', desc: 'Evaluating sprint deadlines and schedule pacing' },
  { name: 'Resource Allocation & Workload', desc: 'Assessing developer allocation and individual capacity' },
  { name: 'Dependency Constraints & Blockers', desc: 'Detecting cross-task dependencies and critical path drags' },
  { name: 'Random Forest Inference Engine', desc: 'Computing delay probability across 100 decision trees' },
  { name: 'AI Action Planning & Recommendations', desc: 'Synthesizing data-grounded action plans and health score' },
];

export const AIRiskAnalysisPage: React.FC = () => {
  const { projects, getAIRiskAnalysis, runAIRiskAnalysis } = useProject();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const queryProjectId = searchParams.get('projectId');
  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    queryProjectId || (projects[0]?.id ?? '1')
  );

  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [pipelineStep, setPipelineStep] = useState<number>(0);
  const [analysisCompleted, setAnalysisCompleted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active analysis data state
  const [analysisData, setAnalysisData] = useState<AIRiskAnalysisResponse | null>(null);

  // Action plan interactive completed items state
  const [completedActions, setCompletedActions] = useState<Record<string, boolean>>({});
  const [activePlanTab, setActivePlanTab] = useState<'today' | 'next_48_hours' | 'before_deadline'>('today');

  // Executive Report Modal state
  const [isReportOpen, setIsReportOpen] = useState<boolean>(false);
  const [reportData, setReportData] = useState<FullAIReportResponse | null>(null);
  const [reportLoading, setReportLoading] = useState<boolean>(false);
  const [copiedReport, setCopiedReport] = useState<boolean>(false);

  const selectedProject = projects.find((p) => p.id === selectedProjectId) || projects[0] || {
    id: '1',
    name: 'Project',
    status: 'On Track',
  };

  // Pipeline animation during analysis
  useEffect(() => {
    let timer: any;
    if (isAnalyzing && !analysisCompleted) {
      timer = setInterval(() => {
        setPipelineStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 160);
    }
    return () => clearInterval(timer);
  }, [isAnalyzing, analysisCompleted]);

  const executeAnalysis = useCallback(async (projId: string) => {
    if (!projId) return;
    setIsAnalyzing(true);
    setAnalysisCompleted(false);
    setPipelineStep(0);
    setError(null);

    try {
      const res = await runAIRiskAnalysis(projId);
      setPipelineStep(5);
      setAnalysisCompleted(true);
      setAnalysisData(res);
      await new Promise((resolve) => setTimeout(resolve, 300));
    } catch (err: any) {
      setError(
        err?.message ||
        'AI risk analysis is temporarily unavailable. Your existing project risk prediction is still accessible.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  }, [runAIRiskAnalysis]);

  useEffect(() => {
    if (queryProjectId && queryProjectId !== selectedProjectId) {
      setSelectedProjectId(queryProjectId);
    }
  }, [queryProjectId]);

  useEffect(() => {
    if (selectedProjectId) {
      // Check existing cached analysis or run fresh
      const existing = getAIRiskAnalysis(selectedProjectId);
      if (existing) {
        setAnalysisData(existing);
      } else {
        executeAnalysis(selectedProjectId);
      }
    }
  }, [selectedProjectId]);

  const handleSelectProject = (projId: string) => {
    setSelectedProjectId(projId);
    setSearchParams({ projectId: projId });
  };

  const toggleAction = (itemText: string) => {
    setCompletedActions((prev) => ({
      ...prev,
      [itemText]: !prev[itemText],
    }));
  };

  const handleOpenReport = async () => {
    setIsReportOpen(true);
    setReportLoading(true);
    setCopiedReport(false);
    try {
      const idNum = parseInt(selectedProjectId.replace(/\D/g, ''), 10) || 1;
      const rep = await api.ai.getAIReport(idNum);
      setReportData(rep);
    } catch {
      // If endpoint fails, fall back to current analysis
    } finally {
      setReportLoading(false);
    }
  };

  const handleCopyReport = () => {
    if (reportData) {
      const repText = `PROJECTPULSE EXECUTIVE AI DOSSIER
Project: ${reportData.project_overview?.name || analysisData?.project_name || 'Project'}
Generated: ${reportData.generated_at}
Health Score: ${reportData.project_health.score}/100 (${reportData.project_health.status})
Risk Level: ${reportData.risk_assessment?.risk_level ?? analysisData?.risk_level} (${reportData.risk_assessment?.risk_score ?? analysisData?.risk_score}%)

EXECUTIVE SUMMARY:
${reportData.executive_summary}

NEXT REVIEW DATE:
${reportData.next_review_date}
`;
      navigator.clipboard.writeText(repText);
      setCopiedReport(true);
      setTimeout(() => setCopiedReport(false), 2500);
      return;
    }
    if (!analysisData) return;
    const textToCopy = `PROJECTPULSE AI RISK INTELLIGENCE REPORT
Project: ${analysisData.project_name}
Evaluated At: ${analysisData.evaluated_at}
Model: ${analysisData.model_name || 'Random Forest Classifier'}

EXECUTIVE SUMMARY:
${analysisData.summary}

PROJECT HEALTH:
Score: ${analysisData.project_health.score}/100 (${analysisData.project_health.status})
Schedule: ${analysisData.project_health.schedule_health}
Workload: ${analysisData.project_health.workload_health}
Budget: ${analysisData.project_health.budget_health}

ML RISK PREDICTION:
Risk Level: ${analysisData.risk_level}
Risk Score: ${analysisData.risk_score}/100
Delay Probability: ${Math.round(analysisData.delay_probability * 100)}%
Expected Delay: ${analysisData.expected_delay_days} Days

TOP RISK DRIVERS:
${analysisData.risk_drivers.map((d) => `• [${d.severity}] ${d.title}: ${d.evidence}`).join('\n')}

PRIORITIZED RECOMMENDATIONS:
${analysisData.recommendations.map((r) => `Priority ${r.priority} — ${r.title}\n  Reason: ${r.reason}\n  Actions: ${r.actions.join(', ')}`).join('\n\n')}

ACTION PLAN:
Today:
${analysisData.action_plan.today.map((a) => `  [ ] ${a}`).join('\n')}
Next 48 Hours:
${analysisData.action_plan.next_48_hours.map((a) => `  [ ] ${a}`).join('\n')}
Before Deadline:
${analysisData.action_plan.before_deadline.map((a) => `  [ ] ${a}`).join('\n')}
`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fade-in pb-12">
      {/* Top Banner & Project Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate(`/projects/${selectedProject.id}`)}
            className="text-xs font-semibold text-gray-500 hover:text-gray-900 inline-flex items-center gap-1.5 mb-1 cursor-pointer transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Project
          </button>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-600" />
              AI Risk Analyst & Intelligence
            </h2>
            <span className="text-[10px] font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-wider">
              Random Forest ML + Real Telemetry
            </span>
          </div>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-semibold text-gray-500 whitespace-nowrap">
            Project:
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => handleSelectProject(e.target.value)}
            className="text-xs font-semibold py-2 px-3 rounded-md border border-gray-300 bg-white text-gray-800 focus:outline-none focus:border-blue-500 shadow-2xs"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.status})
              </option>
            ))}
          </select>

          <Button
            size="sm"
            variant="outline"
            onClick={() => executeAnalysis(selectedProjectId)}
            disabled={isAnalyzing}
            icon={<RefreshCw className={`h-3.5 w-3.5 ${isAnalyzing ? 'animate-spin text-blue-600' : ''}`} />}
          >
            {isAnalyzing ? 'Analyzing...' : 'Re-Analyze'}
          </Button>

          <Button
            size="sm"
            onClick={handleOpenReport}
            disabled={!analysisData || isAnalyzing}
            icon={<FileText className="h-3.5 w-3.5" />}
          >
            Full Report
          </Button>
        </div>
      </div>

      {/* Signature Experience: Intelligent Telemetry Assessment */}
      {isAnalyzing && (
        <div className="p-6 rounded-lg bg-white border border-blue-200/80 shadow-xs space-y-4 animate-slide-up">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-100">
            <div className="flex items-center gap-2.5">
              <div className="h-7 w-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <Sparkles className="h-4 w-4 animate-spin text-blue-600" />
              </div>
              <div>
                <span className="text-[10px] font-bold tracking-wider uppercase text-blue-600 block leading-tight">
                  PROJECTPULSE AI ANALYST
                </span>
                <h4 className="text-xs font-semibold text-gray-900">
                  {analysisCompleted
                    ? 'Intelligence synthesis complete'
                    : `Analyzing schedule risk and team telemetry for ${selectedProject.name}`}
                </h4>
              </div>
            </div>

            <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full w-fit">
              {analysisCompleted ? '✓ Completed' : `Stage ${Math.min(pipelineStep + 1, 5)} of 5`}
            </span>
          </div>

          <div className="space-y-2 pt-1">
            {PIPELINE_SIGNALS.map((sig, idx) => {
              const isDone = idx < pipelineStep || analysisCompleted;
              const isCurrent = idx === pipelineStep && !analysisCompleted;

              return (
                <div
                  key={sig.name}
                  className={`flex items-center justify-between p-2.5 rounded-md border text-xs transition-all duration-200 ${
                    isCurrent
                      ? 'bg-blue-50/70 border-blue-300 shadow-2xs'
                      : isDone
                      ? 'bg-emerald-50/40 border-emerald-200/70 text-emerald-950'
                      : 'bg-gray-50/40 border-gray-100 text-gray-400'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="shrink-0 w-4 text-center font-bold">
                      {isDone ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      ) : isCurrent ? (
                        <span className="text-blue-600 font-bold text-sm inline-block animate-pulse">→</span>
                      ) : (
                        <span className="text-gray-300">·</span>
                      )}
                    </span>
                    <span
                      className={`font-semibold capitalize truncate ${
                        isCurrent ? 'text-blue-900' : isDone ? 'text-gray-800' : 'text-gray-400'
                      }`}
                    >
                      {sig.name}
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-medium hidden sm:block ${
                      isCurrent ? 'text-blue-600 font-semibold' : isDone ? 'text-emerald-700' : 'text-gray-400'
                    }`}
                  >
                    {isDone ? 'Evaluated' : isCurrent ? 'Computing...' : 'Queued'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Actionable Error State */}
      {error && !isAnalyzing && (
        <div className="p-6 rounded-lg bg-white border border-rose-200 shadow-2xs text-center space-y-3 animate-slide-up">
          <AlertTriangle className="h-8 w-8 text-rose-500 mx-auto" />
          <div>
            <h4 className="text-sm font-bold text-gray-900">Analysis Temporarily Unavailable</h4>
            <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">{error}</p>
          </div>
          <div className="pt-1">
            <Button size="sm" variant="outline" onClick={() => executeAnalysis(selectedProjectId)}>
              Try Again
            </Button>
          </div>
        </div>
      )}

      {/* Main Analysis Experience */}
      {analysisData && !isAnalyzing && (
        <div className="space-y-6 animate-fade-in">
          {/* Phase 8: Executive Summary Banner */}
          <div className="p-5 rounded-lg bg-gradient-to-r from-blue-50/90 via-indigo-50/80 to-blue-50/90 border border-blue-200/80 shadow-2xs space-y-2 animate-slide-up">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-blue-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-blue-900">
                  AI Risk Analyst Executive Summary
                </h3>
              </div>
              <span className="text-[11px] text-gray-500 font-medium">
                Evaluated: {analysisData.evaluated_at}
              </span>
            </div>
            <p className="text-xs sm:text-sm font-medium text-gray-900 leading-relaxed">
              {analysisData.summary}
            </p>
          </div>

          {/* Primary 5-Card Intelligence Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {/* 1. Project Health Score (Phase 11) */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                  Project Health
                </span>
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    analysisData.project_health.status === 'Healthy'
                      ? 'bg-emerald-100 text-emerald-800'
                      : analysisData.project_health.status === 'Needs Attention'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {analysisData.project_health.status}
                </span>
              </div>
              <span className="text-xl font-bold text-gray-900 mt-1 block">
                <AnimatedNumber value={analysisData.project_health.score} /> / 100
              </span>
              <span className="text-[11px] text-gray-500 mt-0.5 block truncate">
                {analysisData.project_health.schedule_health}
              </span>
            </div>

            {/* 2. ML Risk Level */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-2">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                ML Risk Level
              </span>
              <span
                className={`text-xl font-bold mt-1 block ${
                  analysisData.risk_level === 'HIGH'
                    ? 'text-rose-600'
                    : analysisData.risk_level === 'MEDIUM'
                    ? 'text-amber-600'
                    : 'text-emerald-600'
                }`}
              >
                {analysisData.risk_level}
              </span>
              <span className="text-[11px] text-gray-500 mt-0.5 block">
                Random Forest
              </span>
            </div>

            {/* 3. ML Risk Score */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-3">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                Risk Score
              </span>
              <span className="text-xl font-bold text-gray-900 mt-1 block">
                <AnimatedNumber value={analysisData.risk_score} /> / 100
              </span>
              <span className="text-[11px] text-gray-500 mt-0.5 block">
                Composite Index
              </span>
            </div>

            {/* 4. Delay Probability */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-4">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                Delay Prob.
              </span>
              <span className="text-xl font-bold text-gray-900 mt-1 block">
                <AnimatedNumber value={Math.round(analysisData.delay_probability * 100)} />%
              </span>
              <span className="text-[11px] text-gray-500 mt-0.5 block">
                Class 1 Probability
              </span>
            </div>

            {/* 5. Expected Delay */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-4 col-span-2 sm:col-span-1">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                Expected Delay
              </span>
              <span className="text-xl font-bold text-rose-600 mt-1 block">
                {analysisData.expected_delay_days} Days
              </span>
              <span className="text-[11px] text-gray-500 mt-0.5 block">
                Forecasted Slippage
              </span>
            </div>
          </div>

          {/* Phase 9: Risk Improvement Loop (KEY PRODUCT FEATURE) */}
          <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-2xs space-y-3 animate-slide-up">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-600" />
                <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                  Risk Improvement Loop & Delta Tracking
                </h3>
              </div>
              <span className="text-[11px] text-gray-500">
                Action → Measurement Feedback Loop
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              {/* Left: Previous vs Current comparison */}
              <div className="flex items-center gap-4 p-3 rounded-md bg-gray-50 border border-gray-100 text-xs">
                <div>
                  <span className="text-gray-400 block text-[11px]">Before Action</span>
                  <span className="font-bold text-gray-700 text-sm mt-0.5 block">
                    {analysisData.risk_comparison.previous_score !== null
                      ? `${analysisData.risk_comparison.previous_score} pts`
                      : 'Initial'}
                  </span>
                </div>

                <span className="text-gray-300 font-bold text-lg">→</span>

                <div>
                  <span className="text-gray-400 block text-[11px]">After Action</span>
                  <span className="font-bold text-gray-900 text-sm mt-0.5 block">
                    {analysisData.risk_score} pts
                  </span>
                </div>

                <div className="ml-auto">
                  {analysisData.risk_comparison.previous_score !== null ? (
                    analysisData.risk_comparison.score_delta < 0 ? (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100/90 px-2 py-1 rounded-full">
                        <TrendingDown className="h-3.5 w-3.5" />
                        ↓ {Math.abs(analysisData.risk_comparison.score_delta)} pts
                      </span>
                    ) : analysisData.risk_comparison.score_delta > 0 ? (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-100/90 px-2 py-1 rounded-full">
                        <TrendingUp className="h-3.5 w-3.5" />
                        ↑ {analysisData.risk_comparison.score_delta} pts
                      </span>
                    ) : (
                      <span className="text-xs font-semibold text-gray-600 bg-gray-200 px-2 py-1 rounded-full">
                        Steady (0 pts)
                      </span>
                    )
                  ) : (
                    <span className="text-[11px] font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                      Baseline Set
                    </span>
                  )}
                </div>
              </div>

              {/* Center & Right: Feedback narrative */}
              <div className="md:col-span-2 text-xs text-gray-700 space-y-1">
                <p className="font-semibold text-gray-900">
                  {analysisData.risk_comparison.comparison_text}
                </p>
                <p className="text-[11px] text-gray-500">
                  Tip: Reassign overloaded tasks, resolve blockers, then click <strong>Re-Analyze</strong> to measure whether risk improved.
                </p>
              </div>
            </div>
          </div>

          {/* 2-Column Split: Telemetry & Gauge (Left 1 Col) | Factors & Recommendations (Right 2 Col) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Radial Risk Gauge + Telemetry + Trend */}
            <div className="space-y-6">
              {/* Radial Risk Gauge */}
              <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col items-center justify-center shadow-2xs text-center motion-card-hover animate-slide-up">
                <RiskGauge
                  score={analysisData.risk_score}
                  level={analysisData.risk_level}
                  delayProbability={Math.round(analysisData.delay_probability * 100)}
                  expectedDelay={`${analysisData.expected_delay_days} Days`}
                  size="md"
                />
                <div className="mt-4 pt-4 border-t border-gray-100 w-full text-center">
                  <span className="text-[11px] text-gray-400 block">Model Engine</span>
                  <span className="text-xs font-medium text-gray-700 block mt-0.5">
                    {analysisData.model_name || 'Random Forest Classifier'}
                  </span>
                </div>
              </div>

              {/* What the Project Data Says (Telemetry Metrics) */}
              <Card
                title="What the Project Data Says"
                subtitle="Real operational telemetry grounding this evaluation"
              >
                <div className="space-y-2.5 pt-1 text-xs">
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <span className="text-gray-500">Overdue Tasks</span>
                    <span className={`font-bold ${analysisData.project_metrics.overdue_tasks > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                      {analysisData.project_metrics.overdue_tasks} items
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <span className="text-gray-500">Task Completion</span>
                    <span className="font-semibold text-gray-900">
                      {analysisData.project_metrics.completed_tasks} / {analysisData.project_metrics.total_tasks} ({analysisData.project_metrics.completion_rate}%)
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <span className="text-gray-500">Days to Deadline</span>
                    <span className={`font-semibold ${analysisData.project_metrics.days_remaining <= 10 ? 'text-amber-600' : 'text-gray-900'}`}>
                      {analysisData.project_metrics.days_remaining} calendar days
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <span className="text-gray-500">Team Size & Capacity</span>
                    <span className="font-semibold text-gray-900">
                      {analysisData.project_metrics.team_size} members ({analysisData.project_metrics.overloaded_members} overloaded)
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <span className="text-gray-500">Average Workload</span>
                    <span className="font-semibold text-gray-900">
                      {analysisData.project_metrics.avg_workload} hrs / member
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1">
                    <span className="text-gray-500">Budget Utilization</span>
                    <span className="font-semibold text-gray-900">
                      {analysisData.project_metrics.budget_utilization}%
                    </span>
                  </div>
                </div>
              </Card>

              {/* Phase 10: Risk History Trend */}
              <Card
                title="Risk History & Trend"
                subtitle="Historical score progression across recent evaluations"
              >
                <div className="space-y-2 pt-1 text-xs">
                  {analysisData.risk_history.slice(-5).map((snap, idx) => (
                    <div
                      key={snap.id || idx}
                      className="flex items-center justify-between p-2 rounded-md bg-gray-50/80 border border-gray-100"
                    >
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3 text-gray-400" />
                        <span className="font-medium text-gray-700">{snap.date}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900">{snap.score} pts</span>
                        <span
                          className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                            snap.level === 'HIGH'
                              ? 'bg-rose-100 text-rose-800'
                              : snap.level === 'MEDIUM'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {snap.level}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Right Column: Why At Risk, Drivers, Recommendations, Action Plan */}
            <div className="lg:col-span-2 space-y-6">
              {/* Phase 3: "WHY IS THIS PROJECT AT RISK?" */}
              <Card
                title="Why is this Project at Risk?"
                subtitle="Empirical operational factors driving the schedule delay forecast"
              >
                <div className="space-y-3 pt-1">
                  {analysisData.risk_factors.map((factor, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-md bg-gray-50/70 border border-gray-200/80 text-xs space-y-1 motion-card-hover"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900 text-sm">{idx + 1}. {factor.title}</span>
                          <span className="text-[10px] text-gray-500 font-medium bg-gray-200/70 px-1.5 py-0.5 rounded">
                            {factor.category}
                          </span>
                        </div>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            factor.impact === 'HIGH'
                              ? 'bg-rose-100 text-rose-800'
                              : factor.impact === 'MEDIUM'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          Impact: {factor.impact}
                        </span>
                      </div>
                      <p className="text-gray-700 leading-relaxed pt-0.5">{factor.evidence}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Phase 4: Risk Contribution & Drivers */}
              <Card
                title="Risk Drivers & Contribution"
                subtitle="Relative contribution percentages calculated from model features and project variance"
              >
                <div className="space-y-3.5 pt-1">
                  {analysisData.risk_drivers.map((driver, idx) => (
                    <div key={idx} className="space-y-1.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-800">{driver.title}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900">{driver.contribution_score}%</span>
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                              driver.severity === 'HIGH'
                                ? 'bg-rose-100 text-rose-700'
                                : driver.severity === 'MEDIUM'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-emerald-100 text-emerald-700'
                            }`}
                          >
                            {driver.severity}
                          </span>
                        </div>
                      </div>

                      {/* Visual contribution bar */}
                      <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            driver.severity === 'HIGH'
                              ? 'bg-rose-500'
                              : driver.severity === 'MEDIUM'
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          }`}
                          style={{ width: `${driver.contribution_score}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-gray-500">{driver.evidence}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Phase 5: AI Recommendation Engine */}
              <Card
                title="What Should We Do? (AI Recommendations)"
                subtitle="Prioritized, actionable interventions grounded in current project conditions"
              >
                <div className="space-y-4 pt-1">
                  {analysisData.recommendations.map((rec) => (
                    <div
                      key={rec.priority}
                      className="p-4 rounded-lg bg-blue-50/50 border border-blue-200/70 text-xs space-y-2 motion-card-hover"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-blue-900 text-sm flex items-center gap-1.5">
                          <span className="h-5 w-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                            {rec.priority}
                          </span>
                          {rec.title}
                        </span>
                        <span className="text-[10px] font-semibold uppercase text-blue-700 tracking-wider">
                          Priority {rec.priority}
                        </span>
                      </div>

                      <p className="text-gray-700 leading-relaxed font-medium">{rec.reason}</p>

                      <div className="pt-1 space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                          Recommended Actions:
                        </span>
                        <ul className="space-y-1 pl-1">
                          {rec.actions.map((act, actIdx) => (
                            <li key={actIdx} className="flex items-start gap-1.5 text-gray-800">
                              <span className="text-blue-600 font-bold">›</span>
                              <span>{act}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Phase 6: Structured Action Plan */}
              <Card
                title="Structured Action Plan"
                subtitle="Tactical checklist for project managers and developers"
              >
                <div className="space-y-3 pt-1">
                  {/* Tab Selector */}
                  <div className="flex border-b border-gray-200">
                    <button
                      onClick={() => setActivePlanTab('today')}
                      className={`pb-2 px-3 text-xs font-semibold border-b-2 cursor-pointer transition-colors ${
                        activePlanTab === 'today'
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      TODAY ({analysisData.action_plan.today.length})
                    </button>
                    <button
                      onClick={() => setActivePlanTab('next_48_hours')}
                      className={`pb-2 px-3 text-xs font-semibold border-b-2 cursor-pointer transition-colors ${
                        activePlanTab === 'next_48_hours'
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      NEXT 48 HOURS ({analysisData.action_plan.next_48_hours.length})
                    </button>
                    <button
                      onClick={() => setActivePlanTab('before_deadline')}
                      className={`pb-2 px-3 text-xs font-semibold border-b-2 cursor-pointer transition-colors ${
                        activePlanTab === 'before_deadline'
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      BEFORE DEADLINE ({analysisData.action_plan.before_deadline.length})
                    </button>
                  </div>

                  {/* Checklist items */}
                  <div className="space-y-2 pt-2">
                    {(analysisData.action_plan[activePlanTab] || []).map((item, iIdx) => {
                      const isChecked = Boolean(completedActions[item]);
                      return (
                        <div
                          key={iIdx}
                          onClick={() => toggleAction(item)}
                          className={`flex items-start gap-2.5 p-2.5 rounded-md border text-xs cursor-pointer transition-all duration-150 ${
                            isChecked
                              ? 'bg-emerald-50/60 border-emerald-200 text-gray-400 line-through'
                              : 'bg-white border-gray-200 text-gray-800 hover:border-blue-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="flex-1 font-medium">{item}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* Phase 12: Full AI Report Modal */}
      <Modal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        title="ProjectPulse — Executive AI Project Risk Report"
        description="Comprehensive intelligence dossier including health index, risk drivers, and action roadmap"
        maxWidth="3xl"
      >
        <div className="space-y-6 max-h-[75vh] overflow-y-auto p-1 text-xs">
          {reportLoading ? (
            <div className="py-12 text-center text-gray-500">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-blue-600" />
              Generating executive dossier...
            </div>
          ) : analysisData ? (
            <div className="space-y-5 print:p-0">
              {/* Report Header Metadata */}
              <div className="p-4 rounded-md bg-gray-50 border border-gray-200 flex flex-wrap justify-between gap-3">
                <div>
                  <h3 className="text-base font-bold text-gray-900">{reportData?.project_overview?.name || analysisData.project_name}</h3>
                  <span className="text-[11px] text-gray-500">
                    Generated: {reportData?.generated_at || analysisData.evaluated_at} • Model: {analysisData.model_name || 'Random Forest Classifier'}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-gray-900 block">
                    Health: {(reportData?.project_health || analysisData.project_health).score}/100 ({(reportData?.project_health || analysisData.project_health).status})
                  </span>
                  <span className={`text-xs font-bold ${
                    analysisData.risk_level === 'HIGH' ? 'text-rose-600' : analysisData.risk_level === 'MEDIUM' ? 'text-amber-600' : 'text-emerald-600'
                  }`}>
                    {analysisData.risk_level} RISK (Score: {analysisData.risk_score}%)
                  </span>
                </div>
              </div>

              {/* 1. Executive Summary */}
              <div className="space-y-1.5">
                <h4 className="font-bold text-gray-900 uppercase tracking-wider text-[11px]">
                  1. Executive Summary
                </h4>
                <p className="text-gray-700 leading-relaxed p-3 rounded-md bg-blue-50/60 border border-blue-200/60">
                  {analysisData.summary}
                </p>
              </div>

              {/* 2. Project Health & Risk Assessment */}
              <div className="space-y-1.5">
                <h4 className="font-bold text-gray-900 uppercase tracking-wider text-[11px]">
                  2. Project Health & Delay Forecast
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div className="p-2.5 rounded border border-gray-200">
                    <span className="text-gray-400 block text-[10px]">Health Score</span>
                    <span className="font-bold text-gray-900 text-sm">{analysisData.project_health.score}/100</span>
                  </div>
                  <div className="p-2.5 rounded border border-gray-200">
                    <span className="text-gray-400 block text-[10px]">Delay Probability</span>
                    <span className="font-bold text-gray-900 text-sm">{Math.round(analysisData.delay_probability * 100)}%</span>
                  </div>
                  <div className="p-2.5 rounded border border-gray-200">
                    <span className="text-gray-400 block text-[10px]">Expected Delay</span>
                    <span className="font-bold text-rose-600 text-sm">{analysisData.expected_delay_days} Days</span>
                  </div>
                  <div className="p-2.5 rounded border border-gray-200">
                    <span className="text-gray-400 block text-[10px]">Days to Deadline</span>
                    <span className="font-bold text-gray-900 text-sm">{analysisData.project_metrics.days_remaining} Days</span>
                  </div>
                </div>
              </div>

              {/* 3. Why the Project is at Risk */}
              <div className="space-y-1.5">
                <h4 className="font-bold text-gray-900 uppercase tracking-wider text-[11px]">
                  3. Key Risk Factors
                </h4>
                <div className="space-y-1.5">
                  {analysisData.risk_factors.map((f, i) => (
                    <div key={i} className="p-2 rounded border border-gray-200 flex justify-between gap-2">
                      <div>
                        <span className="font-bold text-gray-900">{f.title}: </span>
                        <span className="text-gray-700">{f.evidence}</span>
                      </div>
                      <span className="font-bold shrink-0 text-gray-600">[{f.impact}]</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 4. Top Drivers */}
              <div className="space-y-1.5">
                <h4 className="font-bold text-gray-900 uppercase tracking-wider text-[11px]">
                  4. Top Risk Drivers
                </h4>
                <div className="space-y-1">
                  {analysisData.risk_drivers.map((d, i) => (
                    <div key={i} className="flex justify-between py-1 border-b border-gray-100">
                      <span className="text-gray-800 font-medium">{d.title}</span>
                      <span className="font-bold text-gray-900">{d.contribution_score}% ({d.severity})</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 5. Recommendations */}
              <div className="space-y-1.5">
                <h4 className="font-bold text-gray-900 uppercase tracking-wider text-[11px]">
                  5. Actionable Recommendations
                </h4>
                <div className="space-y-2">
                  {analysisData.recommendations.map((r) => (
                    <div key={r.priority} className="p-2.5 rounded bg-gray-50 border border-gray-200">
                      <span className="font-bold text-gray-900">Priority {r.priority}: {r.title}</span>
                      <p className="text-gray-700 mt-0.5">{r.reason}</p>
                      <p className="text-gray-600 text-[11px] mt-1 font-medium">
                        Actions: {r.actions.join(' • ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2 pt-4 border-t border-gray-200">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyReport}
                  icon={copiedReport ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                >
                  {copiedReport ? 'Copied to Clipboard!' : 'Copy Dossier'}
                </Button>

                <Button
                  size="sm"
                  onClick={() => window.print()}
                  icon={<Printer className="h-3.5 w-3.5" />}
                >
                  Print Report
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </Modal>

      {/* Footer Navigation */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/projects/${selectedProject.id}`)}
          icon={<ArrowLeft className="h-4 w-4" />}
        >
          Back to Project Details
        </Button>

        <Button
          size="sm"
          onClick={() => navigate(`/prediction-details?projectId=${selectedProject.id}`)}
          icon={<FileText className="h-4 w-4" />}
        >
          View ML Specification
        </Button>
      </div>
    </div>
  );
};
