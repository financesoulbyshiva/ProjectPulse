import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Cpu,
  Database,
  Layers,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const PredictionDetailsPage: React.FC = () => {
  const { projects, getPrediction, predictProjectRisk } = useProject();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const queryProjectId = searchParams.get('projectId');
  const activeProject = projects.find((p) => p.id === queryProjectId) || projects[0] || { id: '1', name: 'Project' };

  const prediction = getPrediction(activeProject.id);

  useEffect(() => {
    if (!prediction && activeProject.id) {
      predictProjectRisk(activeProject.id).catch(() => {});
    }
  }, [prediction, activeProject.id, predictProjectRisk]);

  const inputs = prediction?.inputs || {
    teamSize: activeProject.teamSize || 4,
    totalTasks: 20,
    completedTasks: 12,
    pendingTasks: 8,
    avgWorkload: 35.0,
    estimatedHours: 240,
    actualHours: 180,
    deadlineDaysRemaining: 25,
    previousDelays: 1,
    budgetUtilization: 75.0,
    taskComplexity: 2.0,
    dependencies: 3,
  };

  const featureList = [
    { name: 'Team Size', value: `${inputs.teamSize} active members`, description: 'Total assigned engineers' },
    { name: 'Total Tasks', value: `${inputs.totalTasks} tasks`, description: 'Total work item backlog' },
    { name: 'Completed Tasks', value: `${inputs.completedTasks} completed`, description: 'Delivered milestones' },
    { name: 'Pending Tasks', value: `${inputs.pendingTasks} remaining`, description: 'Active & to-do items' },
    { name: 'Average Workload', value: `${inputs.avgWorkload} hrs / member`, description: 'Remaining effort per engineer' },
    { name: 'Estimated Hours', value: `${inputs.estimatedHours} hrs`, description: 'Initial baseline sizing' },
    { name: 'Actual Hours Logged', value: `${inputs.actualHours} hrs`, description: 'Realized engineering effort' },
    { name: 'Deadline Days Remaining', value: `${inputs.deadlineDaysRemaining} days`, description: 'Schedule delivery runway' },
    { name: 'Previous Delays', value: `${inputs.previousDelays} occurrences`, description: 'Historical schedule friction' },
    { name: 'Budget Utilization', value: `${inputs.budgetUtilization}%`, description: 'Actual spend vs. allocation' },
    { name: 'Task Complexity', value: `${inputs.taskComplexity} / 3.0`, description: 'Mean technical difficulty' },
    { name: 'Dependencies', value: `${inputs.dependencies} blocked links`, description: 'Predecessor task constraints' },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-fade-in">
      {/* Top Breadcrumb */}
      <div>
        <button
          onClick={() => navigate(`/risk-analysis?projectId=${activeProject.id}`)}
          className="text-xs font-semibold text-gray-500 hover:text-gray-900 inline-flex items-center gap-1.5 mb-1"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to AI Risk Analysis
        </button>
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-gray-900">Technical ML Prediction Details</h2>
          <span className="text-[10px] font-semibold bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded-full">
            Specification
          </span>
        </div>
      </div>

      {/* Visual ML Pipeline */}
      <div className="animate-slide-up stagger-1">
        <Card
          title="Predictive Inference Pipeline"
          subtitle="End-to-end telemetry transformation from raw project state to probabilistic delay output"
        >
          <div className="relative py-3">
            {/* Ambient Data Flow Beam Track connecting the nodes */}
            <div
              className="hidden sm:block absolute top-[32px] left-[12%] right-[12%] h-[2px] bg-slate-200 rounded-full data-flow-track z-0 pointer-events-none"
              aria-hidden="true"
            />

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 relative z-10">
              {/* Step 1 */}
              <div className="flex flex-col items-center p-3.5 rounded-lg border border-gray-200 bg-white sm:bg-white/95 text-center motion-card-hover backdrop-blur-xs">
                <div className="h-9 w-9 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center mb-2 shadow-2xs">
                  <Database className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold text-gray-900">1. Project Data</span>
                <span className="text-[11px] text-gray-500 mt-0.5">DB entities & tasks</span>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col items-center p-3.5 rounded-lg border border-gray-200 bg-white sm:bg-white/95 text-center motion-card-hover backdrop-blur-xs">
                <div className="h-9 w-9 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center mb-2 shadow-2xs">
                  <Layers className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold text-gray-900">2. Feature Engineering</span>
                <span className="text-[11px] text-gray-500 mt-0.5">12-dimensional vector</span>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col items-center p-3.5 rounded-lg border border-blue-200 bg-blue-50/50 sm:bg-blue-50/70 text-center motion-card-hover backdrop-blur-xs">
                <div className="relative">
                  <div className="h-9 w-9 rounded-full bg-blue-600 text-white flex items-center justify-center mb-2 shadow-xs">
                    <Cpu className="h-4 w-4" />
                  </div>
                  <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                    <span className="telemetry-beacon absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                  </span>
                </div>
                <span className="text-xs font-bold text-blue-900">3. ML Model</span>
                <span className="text-[11px] text-blue-700 mt-0.5">Random Forest</span>
              </div>

              {/* Step 4 */}
              <div className="flex flex-col items-center p-3.5 rounded-lg border border-gray-200 bg-white sm:bg-white/95 text-center motion-card-hover backdrop-blur-xs">
                <div className="h-9 w-9 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mb-2 shadow-2xs">
                  <Sparkles className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold text-gray-900">4. Risk Prediction</span>
                <span className="text-[11px] text-gray-500 mt-0.5">Score & Recs</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Model Specification & Predictions Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up stagger-2">
        {/* Model Architecture */}
        <Card
          title="Model Architecture"
          subtitle="Supervised ensemble configuration"
        >
          <div className="space-y-3 pt-1 text-xs">
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Estimator Algorithm</span>
              <span className="font-bold text-gray-900">Random Forest Classifier</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Number of Trees</span>
              <span className="font-semibold text-gray-800">100 Estimators</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Splitting Criterion</span>
              <span className="font-semibold text-gray-800">Gini Impurity</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Max Depth</span>
              <span className="font-semibold text-gray-800">6 (Regularized)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-gray-500">Feature Count ($d$)</span>
              <span className="font-semibold text-gray-800">12 Dimensional</span>
            </div>
          </div>
        </Card>

        {/* Prediction Summary */}
        <Card
          title="Prediction Output"
          subtitle={`Current inferred risk for ${activeProject.name}`}
        >
          <div className="space-y-3 pt-1 text-xs">
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Delay Probability</span>
              <span className="font-bold text-gray-900">{prediction?.delayProbability ?? 0}%</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Standardized Risk Score</span>
              <span
                className={`font-bold ${
                  prediction?.riskLevel === 'HIGH'
                    ? 'text-rose-600'
                    : prediction?.riskLevel === 'MEDIUM'
                    ? 'text-amber-600'
                    : 'text-emerald-600'
                }`}
              >
                {prediction?.riskScore ?? 0} / 100
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Classified Risk Level</span>
              <span
                className={`font-bold ${
                  prediction?.riskLevel === 'HIGH'
                    ? 'text-rose-600'
                    : prediction?.riskLevel === 'MEDIUM'
                    ? 'text-amber-600'
                    : 'text-emerald-600'
                }`}
              >
                {prediction?.riskLevel || 'LOW'}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500">Expected Schedule Delay</span>
              <span className="font-bold text-gray-900">{prediction?.expectedDelay || '0 Days'}</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-gray-500">Explainability Mechanism</span>
              <span className="font-semibold text-blue-600">Decision Path Heuristics</span>
            </div>
          </div>
        </Card>
      </div>

      {/* 12 Features Input Table */}
      <Card
        title="Input Features Specification (12 Predictors)"
        subtitle="Operational metrics extracted from the project database and fed into the model"
      >
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
            <thead className="bg-gray-50/75">
              <tr className="font-semibold uppercase tracking-wider text-gray-400">
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Feature Name</th>
                <th className="py-2.5 px-3">Current Value</th>
                <th className="py-2.5 px-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {featureList.map((f, idx) => (
                <tr key={idx} className="hover:bg-gray-50/50">
                  <td className="py-2.5 px-3 text-gray-400 font-mono">{idx + 1}</td>
                  <td className="py-2.5 px-3 font-semibold text-gray-900">{f.name}</td>
                  <td className="py-2.5 px-3 font-bold text-blue-700 bg-blue-50/30 font-mono">
                    {f.value}
                  </td>
                  <td className="py-2.5 px-3 text-gray-500">{f.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Model Evaluation Metrics Banner (Verified Phase 3 Results) */}
      <div className="p-4 rounded-lg border border-gray-200 bg-white shadow-2xs space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-gray-100">
          <div className="flex items-center gap-1.5 text-xs font-bold text-gray-800">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>Verified Holdout Model Performance Benchmark</span>
          </div>
          <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
            Trained Random Forest (N=84 Test Set)
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200/60">
            <span className="text-[11px] text-gray-500 block">Accuracy</span>
            <span className="text-base font-bold text-gray-900 mt-0.5 block">84.52%</span>
          </div>
          <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200/60">
            <span className="text-[11px] text-gray-500 block">Precision</span>
            <span className="text-base font-bold text-gray-900 mt-0.5 block">78.95%</span>
          </div>
          <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200/60">
            <span className="text-[11px] text-gray-500 block">Recall</span>
            <span className="text-base font-bold text-emerald-700 mt-0.5 block">85.71%</span>
          </div>
          <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200/60">
            <span className="text-[11px] text-gray-500 block">F1-Score</span>
            <span className="text-base font-bold text-blue-700 mt-0.5 block">82.19%</span>
          </div>
        </div>
      </div>

      {/* Bottom Back Button */}
      <div className="flex justify-start">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/risk-analysis?projectId=${activeProject.id}`)}
          icon={<ArrowLeft className="h-4 w-4" />}
        >
          Return to AI Risk Analysis
        </Button>
      </div>
    </div>
  );
};
