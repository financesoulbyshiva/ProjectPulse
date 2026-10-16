import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Users,
  Plus,
  BrainCircuit,
  Sparkles,
  ShieldAlert,
  IndianRupee,
} from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Progress } from '../components/common/Progress';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import type { TaskStatus, TaskPriority } from '../types';

export const ProjectDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { projects, tasks, teamMembers, addTask, updateTaskStatus, updateProject } = useProject();

  const project = projects.find((p) => p.id === id);

  // Modal States
  const [isAddTaskOpen, setIsAddTaskOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);

  // New Task form state
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskAssignedTo, setTaskAssignedTo] = useState(project?.teamMembers[0] || 'Unassigned');
  const [taskPriority, setTaskPriority] = useState<TaskPriority>('Medium');
  const [taskDueDate, setTaskDueDate] = useState('2026-10-25');
  const [taskHours, setTaskHours] = useState('12');

  // Edit Project form state
  const [editStatus, setEditStatus] = useState(project?.status || 'On Track');
  const [editProgress, setEditProgress] = useState(String(project?.progress || 0));

  if (!project) {
    return (
      <div className="py-12 text-center space-y-4">
        <h3 className="text-lg font-bold text-gray-900">Project Not Found</h3>
        <p className="text-sm text-gray-500">The requested project identifier does not exist.</p>
        <Button onClick={() => navigate('/projects')}>Return to Projects</Button>
      </div>
    );
  }

  // Filter tasks belonging to this project
  const projectTasks = tasks.filter((t) => t.projectId === project.id);

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;

    await addTask({
      projectId: project.id,
      projectName: project.name,
      title: taskTitle,
      description: taskDescription,
      assignedTo: taskAssignedTo,
      priority: taskPriority,
      dueDate: taskDueDate,
      status: 'To Do',
      estimatedHours: Number(taskHours) || 8,
      complexity: 2,
      hasDependencies: false,
    });

    setIsAddTaskOpen(false);
    setTaskTitle('');
    setTaskDescription('');
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProject(project.id, {
      status: editStatus,
      progress: Math.min(100, Math.max(0, Number(editProgress))),
    });
    setIsEditOpen(false);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top breadcrumb & actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/projects')}
            className="text-xs font-semibold text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Projects
          </button>
          <span className="text-gray-300">/</span>
          <span className="text-xs font-semibold text-gray-900">{project.name}</span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setEditStatus(project.status);
              setEditProgress(String(project.progress));
              setIsEditOpen(true);
            }}
          >
            Edit Project
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate(`/risk-analysis?projectId=${project.id}`)}
            icon={<BrainCircuit className="h-4 w-4 text-blue-600" />}
          >
            View AI Risk Analysis
          </Button>

          <Button
            size="sm"
            onClick={() => setIsAddTaskOpen(true)}
            icon={<Plus className="h-4 w-4" />}
          >
            Add Task
          </Button>
        </div>
      </div>

      {/* Hero Summary Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-2xs animate-slide-up stagger-1">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-gray-100">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl font-bold text-gray-900">{project.name}</h2>
              <Badge
                variant={
                  project.status === 'Delayed'
                    ? 'danger'
                    : project.status === 'At Risk'
                    ? 'warning'
                    : 'success'
                }
                dot
              >
                {project.status}
              </Badge>
            </div>
            <p className="text-xs text-gray-500 mt-1 max-w-2xl">{project.description}</p>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right">
              <span className="text-xs text-gray-400 block font-medium">Delivery Deadline</span>
              <span className="text-sm font-semibold text-gray-900 flex items-center justify-end gap-1 mt-0.5">
                <Calendar className="h-3.5 w-3.5 text-gray-500" /> {project.deadline}
              </span>
            </div>
          </div>
        </div>

        {/* 4 Metadata Chips */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-5 text-xs">
          <div>
            <span className="text-gray-400 font-medium block">Total Budget</span>
            <span className="text-sm font-bold text-gray-900 mt-0.5 flex items-center gap-0.5">
              <IndianRupee className="h-3.5 w-3.5 text-gray-500" />
              {formatINR(project.budget)}
            </span>
            <span className="text-[11px] text-gray-500 mt-0.5 block">
              Spent: {formatINR(project.actualSpent)}
            </span>
          </div>

          <div>
            <span className="text-gray-400 font-medium block">Overall Progress</span>
            <span className="text-sm font-bold text-gray-900 mt-0.5 block">
              {project.progress}% Complete
            </span>
            <div className="w-28 mt-1.5">
              <Progress value={project.progress} size="sm" />
            </div>
          </div>

          <div>
            <span className="text-gray-400 font-medium block">Engineering Team</span>
            <span className="text-sm font-bold text-gray-900 mt-0.5 flex items-center gap-1">
              <Users className="h-3.5 w-3.5 text-gray-500" />
              {project.teamSize} Members
            </span>
            <span className="text-[11px] text-gray-500 mt-0.5 block">
              Lead: {project.manager}
            </span>
          </div>

          <div>
            <span className="text-gray-400 font-medium block">Risk Assessment</span>
            <span
              className={`text-sm font-bold mt-0.5 inline-flex items-center gap-1 ${
                project.riskSummary?.riskLevel === 'HIGH'
                  ? 'text-rose-600'
                  : project.riskSummary?.riskLevel === 'MEDIUM'
                  ? 'text-amber-600'
                  : 'text-emerald-600'
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              {project.riskSummary?.riskLevel} RISK ({project.riskSummary?.riskScore}%)
            </span>
            <span className="text-[11px] text-gray-500 mt-0.5 block">
              Exp. Slip: {project.riskSummary?.expectedDelay}
            </span>
          </div>
        </div>
      </div>

      {/* 2-Column Split: Tasks Table (Left 2 Col) & Team + Risk Summary (Right 1 Col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Project Tasks */}
        <div className="lg:col-span-2 space-y-6">
          <Card
            title={`Project Tasks (${projectTasks.length})`}
            subtitle="Operational work items and delivery checkpoints"
            action={
              <Button size="sm" variant="outline" onClick={() => setIsAddTaskOpen(true)}>
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Task
              </Button>
            }
          >
            {projectTasks.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-500">
                No tasks assigned to this project yet. Click "Add Task" to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
                  <thead>
                    <tr className="font-semibold text-gray-400 uppercase tracking-wider">
                      <th className="pb-3">Task</th>
                      <th className="pb-3">Assigned To</th>
                      <th className="pb-3">Due Date</th>
                      <th className="pb-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {projectTasks.map((t) => (
                      <tr key={t.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="py-3 pr-4">
                          <span className="font-semibold text-gray-900 block">{t.title}</span>
                          <span className="text-[11px] text-gray-500 block">
                            Priority: {t.priority} • Est: {t.estimatedHours}h
                          </span>
                        </td>
                        <td className="py-3 pr-4 font-medium text-gray-700">{t.assignedTo}</td>
                        <td className="py-3 pr-4 text-gray-500">{t.dueDate}</td>
                        <td className="py-3 text-right">
                          <select
                            value={t.status}
                            onChange={(e) => updateTaskStatus(t.id, e.target.value as TaskStatus)}
                            className="text-xs font-medium rounded border border-gray-300 py-1 px-2 bg-white text-gray-700 focus:outline-none focus:border-blue-500"
                          >
                            <option value="To Do">To Do</option>
                            <option value="In Progress">In Progress</option>
                            <option value="Completed">Completed</option>
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Risk Summary & Team */}
        <div className="space-y-6">
          {/* Risk Summary Widget */}
          <Card
            title="ML Risk Summary"
            subtitle="Probabilistic schedule evaluation"
            action={
              <button
                onClick={() => navigate(`/risk-analysis?projectId=${project.id}`)}
                className="text-xs text-blue-600 font-semibold hover:underline inline-flex items-center gap-1"
              >
                Inspect <Sparkles className="h-3 w-3" />
              </button>
            }
          >
            <div className="space-y-3 pt-1 text-xs">
              <div className="p-3 rounded-md bg-gray-50 border border-gray-200 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Risk Level</span>
                  <span
                    className={`font-bold ${
                      project.riskSummary?.riskLevel === 'HIGH'
                        ? 'text-rose-600'
                        : project.riskSummary?.riskLevel === 'MEDIUM'
                        ? 'text-amber-600'
                        : 'text-emerald-600'
                    }`}
                  >
                    {project.riskSummary?.riskLevel}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Delay Probability</span>
                  <span className="font-semibold text-gray-900">
                    {project.riskSummary?.delayProbability}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Expected Delay</span>
                  <span className="font-bold text-gray-900">
                    {project.riskSummary?.expectedDelay}
                  </span>
                </div>
              </div>

              <p className="text-[11px] text-gray-500 leading-relaxed">
                Evaluated using 12 project telemetry features via scikit-learn Random Forest ensemble.
              </p>
            </div>
          </Card>

          {/* Assigned Team Members */}
          <Card
            title={`Assigned Team (${project.teamMembers.length})`}
            subtitle="Contributors allocated to this initiative"
          >
            <div className="space-y-2.5 pt-1">
              {project.teamMembers.map((mName, i) => {
                const memberData = teamMembers.find((tm) => tm.name === mName);
                return (
                  <div key={i} className="flex items-center justify-between p-2 rounded-md bg-gray-50 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="h-6 w-6 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-[10px]">
                        {mName.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <span className="font-semibold text-gray-800 block">{mName}</span>
                        <span className="text-[10px] text-gray-400 block">{memberData?.role || 'Engineer'}</span>
                      </div>
                    </div>
                    <Badge variant={memberData?.workload === 'High' ? 'danger' : 'neutral'} size="sm">
                      {memberData?.workload || 'Med'} load
                    </Badge>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Add Task Modal */}
      <Modal
        isOpen={isAddTaskOpen}
        onClose={() => setIsAddTaskOpen(false)}
        title="Add Task to Project"
        description={`Creating a task for "${project.name}"`}
      >
        <form onSubmit={handleCreateTask} className="space-y-4">
          <Input
            label="Task Name"
            placeholder="e.g. Implement OAuth Flow"
            value={taskTitle}
            onChange={(e) => setTaskTitle(e.target.value)}
            required
          />

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">Description</label>
            <textarea
              rows={2}
              className="w-full text-xs p-2 rounded-md border border-gray-300 focus:outline-none focus:border-blue-500"
              placeholder="Task details and deliverables..."
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Assigned Member"
              value={taskAssignedTo}
              onChange={(e) => setTaskAssignedTo(e.target.value)}
              options={project.teamMembers.map((m) => ({ value: m, label: m }))}
            />

            <Select
              label="Priority"
              value={taskPriority}
              onChange={(e) => setTaskPriority(e.target.value as TaskPriority)}
              options={[
                { value: 'Low', label: 'Low' },
                { value: 'Medium', label: 'Medium' },
                { value: 'High', label: 'High' },
                { value: 'Critical', label: 'Critical' },
              ]}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Due Date"
              type="date"
              value={taskDueDate}
              onChange={(e) => setTaskDueDate(e.target.value)}
              required
            />

            <Input
              label="Estimated Hours"
              type="number"
              value={taskHours}
              onChange={(e) => setTaskHours(e.target.value)}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsAddTaskOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">
              Save Task
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Project Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Project Status & Progress"
        description="Quickly update progress percentage or status"
      >
        <form onSubmit={handleSaveEdit} className="space-y-4">
          <Select
            label="Project Status"
            value={editStatus}
            onChange={(e) => setEditStatus(e.target.value as any)}
            options={[
              { value: 'On Track', label: 'On Track' },
              { value: 'At Risk', label: 'At Risk' },
              { value: 'Delayed', label: 'Delayed' },
              { value: 'Completed', label: 'Completed' },
            ]}
          />

          <Input
            label="Progress (%)"
            type="number"
            min="0"
            max="100"
            value={editProgress}
            onChange={(e) => setEditProgress(e.target.value)}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">
              Update Project
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
