import React, { useState } from 'react';
import { TrendingUp, Clock, IndianRupee, Users, Filter } from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Card } from '../components/common/Card';
import { SimpleBarChart } from '../components/charts/SimpleBarChart';
import { AnimatedNumber } from '../components/common/AnimatedNumber';

export const AnalyticsPage: React.FC = () => {
  const { projects, tasks, teamMembers } = useProject();

  const [selectedProject, setSelectedProject] = useState('All');
  const [selectedRange, setSelectedRange] = useState('This Quarter');

  // Compute metrics
  const activeProjects = selectedProject === 'All'
    ? projects
    : projects.filter((p) => p.name === selectedProject);

  const activeTasks = selectedProject === 'All'
    ? tasks
    : tasks.filter((t) => t.projectName === selectedProject);

  const avgCompletionRate = activeProjects.length
    ? Math.round(activeProjects.reduce((a, b) => a + b.progress, 0) / activeProjects.length)
    : 0;

  const totalBudget = activeProjects.reduce((a, b) => a + b.budget, 0);
  const totalSpent = activeProjects.reduce((a, b) => a + b.actualSpent, 0);
  const budgetUtilization = totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;

  const completedTasks = activeTasks.filter((t) => t.status === 'Completed').length;
  const inProgressTasks = activeTasks.filter((t) => t.status === 'In Progress').length;
  const todoTasks = activeTasks.filter((t) => t.status === 'To Do').length;

  // Chart 1: Project Progress
  const progressChartItems = activeProjects.map((p) => ({
    label: p.name,
    value: p.progress,
    displayValue: `${p.progress}%`,
    color: p.status === 'Delayed' ? 'bg-rose-500' : p.status === 'At Risk' ? 'bg-amber-500' : 'bg-blue-600',
  }));

  // Chart 2: Task Completion Distribution
  const totalTasksCount = activeTasks.length || 1;
  const taskChartItems = [
    {
      label: 'Completed Tasks',
      value: Math.round((completedTasks / totalTasksCount) * 100),
      displayValue: `${completedTasks} tasks (${Math.round((completedTasks / totalTasksCount) * 100)}%)`,
      color: 'bg-emerald-600',
    },
    {
      label: 'In Progress Tasks',
      value: Math.round((inProgressTasks / totalTasksCount) * 100),
      displayValue: `${inProgressTasks} tasks (${Math.round((inProgressTasks / totalTasksCount) * 100)}%)`,
      color: 'bg-blue-600',
    },
    {
      label: 'To Do Backlog',
      value: Math.round((todoTasks / totalTasksCount) * 100),
      displayValue: `${todoTasks} tasks (${Math.round((todoTasks / totalTasksCount) * 100)}%)`,
      color: 'bg-gray-400',
    },
  ];

  // Chart 3: Team Workload (Hours comparison against 40h standard)
  const workloadChartItems = teamMembers.map((tm) => {
    const hours = tm.allocatedHours || (tm.workload === 'High' ? 44 : tm.workload === 'Medium' ? 32 : 24);
    return {
      label: `${tm.name} (${tm.role.split('&')[0].trim()})`,
      value: hours,
      displayValue: `${hours}h / 40h (${Math.round((hours / 40) * 100)}%)`,
      color: hours > 40 ? 'bg-rose-500' : hours >= 32 ? 'bg-blue-600' : 'bg-emerald-500',
    };
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Filter Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white p-3.5 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <span className="text-xs font-semibold text-gray-700">Filter Scope:</span>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-md border border-gray-300 bg-white text-gray-700 focus:outline-none focus:border-blue-500"
          >
            <option value="All">All Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>

          <select
            value={selectedRange}
            onChange={(e) => setSelectedRange(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-md border border-gray-300 bg-white text-gray-700 focus:outline-none focus:border-blue-500"
          >
            <option value="This Quarter">This Quarter (Q4 2026)</option>
            <option value="Last 30 Days">Last 30 Days</option>
            <option value="All Time">All Time</option>
          </select>
        </div>
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-1">
          <span className="text-xs text-gray-500 font-medium block">Avg Completion Rate</span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-bold text-gray-900">
              <AnimatedNumber value={avgCompletionRate} />%
            </span>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </div>
          <span className="text-[11px] text-gray-400 mt-1 block">Weighted task average</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-2">
          <span className="text-xs text-gray-500 font-medium block">Average Task Delay</span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-bold text-amber-600">1.8 Days</span>
            <Clock className="h-4 w-4 text-amber-600" />
          </div>
          <span className="text-[11px] text-gray-400 mt-1 block">Historical schedule slip</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-3">
          <span className="text-xs text-gray-500 font-medium block">Budget Utilization</span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-bold text-gray-900">
              <AnimatedNumber value={budgetUtilization} />%
            </span>
            <IndianRupee className="h-4 w-4 text-emerald-600" />
          </div>
          <span className="text-[11px] text-gray-400 mt-1 block">₹{totalSpent.toLocaleString()} of ₹{totalBudget.toLocaleString()}</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-2xs motion-card-hover animate-slide-up stagger-4">
          <span className="text-xs text-gray-500 font-medium block">Team Workload Balance</span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-bold text-gray-900">85%</span>
            <Users className="h-4 w-4 text-indigo-600" />
          </div>
          <span className="text-[11px] text-gray-400 mt-1 block">Optimal capacity threshold</span>
        </div>
      </div>

      {/* ONLY THREE Simple Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-slide-up stagger-2">
        {/* Viz 1: Project Progress */}
        <Card
          title="1. Project Progress"
          subtitle="Completion percentages across initiatives"
        >
          <SimpleBarChart items={progressChartItems} />
        </Card>

        {/* Viz 2: Task Completion */}
        <Card
          title="2. Task Completion"
          subtitle="Distribution of work item statuses"
        >
          <SimpleBarChart items={taskChartItems} />
        </Card>

        {/* Viz 3: Team Workload */}
        <Card
          title="3. Team Workload"
          subtitle="Hours assigned vs. 40-hour capacity"
        >
          <SimpleBarChart items={workloadChartItems} maxValue={50} unit="h" />
        </Card>
      </div>
    </div>
  );
};
