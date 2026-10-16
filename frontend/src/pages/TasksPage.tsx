import React, { useState, useMemo } from 'react';
import { Plus, Search, Filter, CheckSquare } from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { EmptyState } from '../components/common/EmptyState';
import type { TaskStatus, TaskPriority } from '../types';

export const TasksPage: React.FC = () => {
  const { tasks, projects, teamMembers, addTask, updateTaskStatus } = useProject();

  const [activeTab, setActiveTab] = useState<'All' | 'To Do' | 'In Progress' | 'Completed'>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [projectFilter, setProjectFilter] = useState('All');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [taskName, setTaskName] = useState('');
  const [taskProject, setTaskProject] = useState(projects[0]?.name || '');
  const [assignedMember, setAssignedMember] = useState(teamMembers[0]?.name || '');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('Medium');
  const [dueDate, setDueDate] = useState('2026-10-25');
  const [hours, setHours] = useState('10');

  // Filter tasks
  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      const matchesTab = activeTab === 'All' || t.status === activeTab;
      const matchesSearch =
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.assignedTo.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.projectName.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesProject = projectFilter === 'All' || t.projectName === projectFilter;

      return matchesTab && matchesSearch && matchesProject;
    });
  }, [tasks, activeTab, searchQuery, projectFilter]);

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskName.trim()) return;

    const matchedProj = projects.find((p) => p.name === taskProject) || projects[0];

    await addTask({
      projectId: matchedProj.id,
      projectName: matchedProj.name,
      title: taskName,
      description,
      assignedTo: assignedMember,
      priority,
      dueDate,
      status: 'To Do',
      estimatedHours: Number(hours) || 8,
      complexity: 2,
      hasDependencies: false,
    });

    setIsModalOpen(false);
    setTaskName('');
    setDescription('');
  };

  const getPriorityBadge = (prio: TaskPriority) => {
    switch (prio) {
      case 'Critical':
        return <Badge variant="danger">Critical</Badge>;
      case 'High':
        return <Badge variant="warning">High</Badge>;
      case 'Medium':
        return <Badge variant="brand">Medium</Badge>;
      case 'Low':
        return <Badge variant="neutral">Low</Badge>;
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Top Filter & Add Task Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Search & Project Filter */}
        <div className="flex flex-1 items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search tasks by name or assignee..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm rounded-md border border-gray-300 bg-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400 hidden sm:block" />
            <select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              className="py-2 px-3 text-sm rounded-md border border-gray-300 bg-white text-gray-700 focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Button onClick={() => setIsModalOpen(true)} icon={<Plus className="h-4 w-4" />}>
          Add Task
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-6 text-sm font-medium">
          {(['All', 'To Do', 'In Progress', 'Completed'] as const).map((tab) => {
            const count =
              tab === 'All' ? tasks.length : tasks.filter((t) => t.status === tab).length;
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
                  isActive
                    ? 'border-blue-600 text-blue-600 font-semibold'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    isActive ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tasks Table */}
      {filteredTasks.length === 0 ? (
        <EmptyState
          title="No tasks match filter"
          message="No tasks found for the selected status tab or search query."
          icon={<CheckSquare className="h-6 w-6 text-gray-400" />}
          actionText="Add New Task"
          onAction={() => setIsModalOpen(true)}
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-2xs">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50/75">
              <tr className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                <th className="px-5 py-3.5">Task</th>
                <th className="px-4 py-3.5">Project</th>
                <th className="px-4 py-3.5">Assigned To</th>
                <th className="px-4 py-3.5">Priority</th>
                <th className="px-4 py-3.5">Due Date</th>
                <th className="px-5 py-3.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {filteredTasks.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50/75 transition-colors">
                  <td className="px-5 py-4">
                    <span className="font-semibold text-gray-900 block">{task.title}</span>
                    {task.description && (
                      <span className="text-xs text-gray-500 block truncate max-w-sm mt-0.5">
                        {task.description}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-4 text-xs font-medium text-gray-700 whitespace-nowrap">
                    {task.projectName}
                  </td>
                  <td className="px-4 py-4 text-xs font-medium text-gray-800 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <div className="h-5 w-5 rounded-full bg-blue-100 text-blue-700 text-[10px] flex items-center justify-center font-bold">
                        {task.assignedTo.slice(0, 1)}
                      </div>
                      <span>{task.assignedTo}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    {getPriorityBadge(task.priority)}
                  </td>
                  <td className="px-4 py-4 text-xs font-medium text-gray-600 whitespace-nowrap">
                    {task.dueDate}
                  </td>
                  <td className="px-5 py-4 text-right whitespace-nowrap">
                    <select
                      value={task.status}
                      onChange={(e) => updateTaskStatus(task.id, e.target.value as TaskStatus)}
                      className={`text-xs font-semibold rounded-md border py-1 px-2.5 bg-white transition-colors cursor-pointer ${
                        task.status === 'Completed'
                          ? 'border-emerald-300 text-emerald-700 bg-emerald-50/50'
                          : task.status === 'In Progress'
                          ? 'border-blue-300 text-blue-700 bg-blue-50/50'
                          : 'border-gray-300 text-gray-700'
                      }`}
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

      {/* Add Task Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Task"
        description="Add a task item to your engineering workflow"
      >
        <form onSubmit={handleAddTask} className="space-y-4">
          <Input
            label="Task Name"
            placeholder="e.g. Build Data Migration Script"
            value={taskName}
            onChange={(e) => setTaskName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Project"
              value={taskProject}
              onChange={(e) => setTaskProject(e.target.value)}
              options={projects.map((p) => ({ value: p.name, label: p.name }))}
            />

            <Select
              label="Assigned Member"
              value={assignedMember}
              onChange={(e) => setAssignedMember(e.target.value)}
              options={teamMembers.map((tm) => ({ value: tm.name, label: tm.name }))}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">Description</label>
            <textarea
              rows={2}
              className="w-full text-xs p-2 rounded-md border border-gray-300 focus:outline-none focus:border-blue-500"
              placeholder="Scope details and verification criteria..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
              options={[
                { value: 'Low', label: 'Low' },
                { value: 'Medium', label: 'Medium' },
                { value: 'High', label: 'High' },
                { value: 'Critical', label: 'Critical' },
              ]}
            />

            <Input
              label="Due Date"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              required
            />
          </div>

          <Input
            label="Estimated Effort (Hours)"
            type="number"
            value={hours}
            onChange={(e) => setHours(e.target.value)}
            required
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">
              Create Task
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
