import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderKanban,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  ShieldAlert,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { SimpleBarChart } from '../components/charts/SimpleBarChart';
import { Progress } from '../components/common/Progress';
import { AnimatedNumber } from '../components/common/AnimatedNumber';

export const DashboardPage: React.FC = () => {
  const { projects, activities } = useProject();
  const navigate = useNavigate();

  // Compute 4 main KPIs
  const activeProjects = projects.filter((p) => p.status === 'On Track' || p.status === 'At Risk' || p.status === 'Delayed').length;
  const completedProjects = projects.filter((p) => p.status === 'Completed').length;
  const atRiskProjects = projects.filter((p) => p.status === 'At Risk' || p.status === 'Delayed').length;
  const overallProgress = projects.length
    ? Math.round(projects.reduce((acc, p) => acc + p.progress, 0) / projects.length)
    : 0;

  // Status badge helper
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'On Track':
        return <Badge variant="success" dot>On Track</Badge>;
      case 'At Risk':
        return <Badge variant="warning" dot>At Risk</Badge>;
      case 'Delayed':
        return <Badge variant="danger" dot>Delayed</Badge>;
      case 'Completed':
        return <Badge variant="brand" dot>Completed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  // Bar chart data for Project Progress
  const projectChartItems = projects.map((p) => ({
    label: p.name,
    value: p.progress,
    displayValue: `${p.progress}%`,
    color: p.status === 'Delayed' ? 'bg-rose-500' : p.status === 'At Risk' ? 'bg-amber-500' : 'bg-blue-600',
  }));

  // Risk Distribution counts
  const highRiskCount = projects.filter((p) => p.riskSummary?.riskLevel === 'HIGH').length;
  const mediumRiskCount = projects.filter((p) => p.riskSummary?.riskLevel === 'MEDIUM').length;
  const lowRiskCount = projects.filter((p) => p.riskSummary?.riskLevel === 'LOW').length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 4 Main KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-2xs flex items-center justify-between motion-card-hover animate-slide-up stagger-1">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Projects</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">
              <AnimatedNumber value={activeProjects} />
            </h3>
            <p className="text-[11px] text-gray-500 mt-0.5">Currently in execution</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <FolderKanban className="h-5 w-5" />
          </div>
        </div>

        {/* KPI 2 */}
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-2xs flex items-center justify-between motion-card-hover animate-slide-up stagger-2">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Completed Projects</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">
              <AnimatedNumber value={completedProjects} />
            </h3>
            <p className="text-[11px] text-emerald-600 font-medium mt-0.5">Delivered to date</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <CheckCircle2 className="h-5 w-5" />
          </div>
        </div>

        {/* KPI 3 */}
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-2xs flex items-center justify-between motion-card-hover animate-slide-up stagger-3">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">At-Risk Projects</p>
            <h3 className="text-2xl font-bold text-rose-600 mt-1">
              <AnimatedNumber value={atRiskProjects} />
            </h3>
            <p className="text-[11px] text-rose-600 font-medium mt-0.5">ML delay predicted</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
            <AlertTriangle className="h-5 w-5" />
          </div>
        </div>

        {/* KPI 4 */}
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-2xs flex items-center justify-between motion-card-hover animate-slide-up stagger-4">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Overall Progress</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">
              <AnimatedNumber value={overallProgress} />%
            </h3>
            <p className="text-[11px] text-blue-600 font-medium mt-0.5">Portfolio average</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Main Grid: Left (Progress Chart & Recent Projects), Right (Risk Overview & Activity) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-6 animate-slide-up stagger-2">
          {/* Project Progress Chart */}
          <Card
            title="Project Progress"
            subtitle="Completion trajectory across portfolio initiatives"
            action={
              <Button size="sm" variant="ghost" onClick={() => navigate('/projects')}>
                View All <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            }
          >
            <SimpleBarChart items={projectChartItems} />
          </Card>

          {/* Recent Projects Table */}
          <Card
            title="Recent Projects"
            subtitle="Status and delivery countdown for active initiatives"
          >
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
                <thead>
                  <tr className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    <th className="pb-3">Project</th>
                    <th className="pb-3 w-32">Progress</th>
                    <th className="pb-3">Deadline</th>
                    <th className="pb-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {projects.slice(0, 4).map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/projects/${p.id}`)}
                      className="cursor-pointer hover:bg-gray-50/75 active:bg-blue-50/40 transition-colors duration-150"
                    >
                      <td className="py-3 pr-4">
                        <span className="font-semibold text-gray-900 block hover:text-blue-600">
                          {p.name}
                        </span>
                        <span className="text-xs text-gray-500 block truncate max-w-xs">
                          {p.manager} • {p.teamSize} members
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="space-y-1">
                          <span className="text-xs font-semibold text-gray-700">{p.progress}%</span>
                          <Progress
                            value={p.progress}
                            size="sm"
                            variant={p.status === 'Delayed' ? 'danger' : p.status === 'At Risk' ? 'warning' : 'brand'}
                          />
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-xs font-medium text-gray-600">
                        {p.deadline}
                      </td>
                      <td className="py-3 text-right">
                        {getStatusBadge(p.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Right Column (1 Col) */}
        <div className="space-y-6 animate-slide-up stagger-3">
          {/* Risk Overview */}
          <Card
            title="Risk Overview"
            subtitle="ML Delay Risk Distribution"
            action={
              <Button size="sm" variant="ghost" onClick={() => navigate('/risk-analysis')}>
                Analyze <Sparkles className="h-3.5 w-3.5 ml-1 text-blue-600" />
              </Button>
            }
          >
            <div className="space-y-3 pt-1">
              <div className="flex items-center justify-between p-3 rounded-md bg-rose-50 border border-rose-200 transition-transform duration-150 hover:translate-x-0.5">
                <div className="flex items-center gap-2.5">
                  <ShieldAlert className="h-4 w-4 text-rose-600" />
                  <span className="text-xs font-semibold text-rose-900">High Risk Projects</span>
                </div>
                <span className="text-sm font-bold text-rose-700">
                  <AnimatedNumber value={highRiskCount} />
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-amber-50 border border-amber-200 transition-transform duration-150 hover:translate-x-0.5">
                <div className="flex items-center gap-2.5">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  <span className="text-xs font-semibold text-amber-900">Medium Risk Projects</span>
                </div>
                <span className="text-sm font-bold text-amber-700">
                  <AnimatedNumber value={mediumRiskCount} />
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-emerald-50 border border-emerald-200 transition-transform duration-150 hover:translate-x-0.5">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span className="text-xs font-semibold text-emerald-900">Low Risk Projects</span>
                </div>
                <span className="text-sm font-bold text-emerald-700">
                  <AnimatedNumber value={lowRiskCount} />
                </span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-gray-100 text-[11px] text-gray-500 flex items-center justify-between">
              <span>Model: Random Forest</span>
              <span className="text-blue-600 font-medium">Explainable ML</span>
            </div>
          </Card>

          {/* Recent Activity */}
          <Card
            title="Recent Activity"
            subtitle="Telemetry and operational log"
          >
            <div className="space-y-3 pt-1">
              {activities.slice(0, 4).map((act) => (
                <div key={act.id} className="flex items-start gap-2.5 text-xs">
                  <div className="mt-0.5 h-1.5 w-1.5 rounded-full bg-blue-600 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-gray-800 leading-snug">
                      <span className="font-semibold text-gray-900">{act.user}</span>{' '}
                      {act.action}{' '}
                      <span className="font-medium text-gray-900">{act.target}</span>
                    </p>
                    <span className="text-[10px] text-gray-400 flex items-center gap-1 mt-0.5">
                      <Clock className="h-2.5 w-2.5" /> {act.timestamp}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
