import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, FolderPlus } from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Progress } from '../components/common/Progress';
import { EmptyState } from '../components/common/EmptyState';
import type { ProjectStatus } from '../types';

export const ProjectsPage: React.FC = () => {
  const { projects } = useProject();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('All');

  // Filter projects
  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      const matchesSearch =
        project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.manager.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus =
        statusFilter === 'All' || project.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [projects, searchQuery, statusFilter]);

  const getStatusBadge = (status: ProjectStatus) => {
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

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Search & Filter */}
        <div className="flex flex-1 items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search projects by name, manager..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm rounded-md border border-gray-300 bg-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400 hidden sm:block" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="py-2 px-3 text-sm rounded-md border border-gray-300 bg-white text-gray-700 focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Statuses</option>
              <option value="On Track">On Track</option>
              <option value="At Risk">At Risk</option>
              <option value="Delayed">Delayed</option>
              <option value="Completed">Completed</option>
            </select>
          </div>
        </div>

        {/* New Project CTA */}
        <Button
          onClick={() => navigate('/projects/create')}
          icon={<Plus className="h-4 w-4" />}
        >
          New Project
        </Button>
      </div>

      {/* Projects Table */}
      {filteredProjects.length === 0 ? (
        <EmptyState
          title="No projects found"
          message={
            searchQuery || statusFilter !== 'All'
              ? 'No projects match your current search or filter query.'
              : 'You have not initialized any projects yet.'
          }
          icon={<FolderPlus className="h-6 w-6 text-gray-400" />}
          actionText={searchQuery ? 'Clear Filters' : 'Create First Project'}
          onAction={() => {
            if (searchQuery || statusFilter !== 'All') {
              setSearchQuery('');
              setStatusFilter('All');
            } else {
              navigate('/projects/create');
            }
          }}
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-2xs">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50/75">
              <tr className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                <th className="px-5 py-3.5">Project</th>
                <th className="px-4 py-3.5">Manager</th>
                <th className="px-4 py-3.5 w-40">Progress</th>
                <th className="px-4 py-3.5">Deadline</th>
                <th className="px-4 py-3.5">Budget</th>
                <th className="px-4 py-3.5">Risk Score</th>
                <th className="px-5 py-3.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {filteredProjects.map((project) => (
                <tr
                  key={project.id}
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="cursor-pointer hover:bg-gray-50/75 active:bg-blue-50/40 transition-colors duration-150"
                >
                  <td className="px-5 py-4">
                    <span className="font-semibold text-gray-900 block hover:text-blue-600">
                      {project.name}
                    </span>
                    <span className="text-xs text-gray-500 block truncate max-w-sm mt-0.5">
                      {project.description}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-xs font-medium text-gray-700">
                    {project.manager}
                  </td>
                  <td className="px-4 py-4">
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs font-medium text-gray-700">
                        <span>{project.progress}%</span>
                      </div>
                      <Progress
                        value={project.progress}
                        size="sm"
                        variant={
                          project.status === 'Delayed'
                            ? 'danger'
                            : project.status === 'At Risk'
                            ? 'warning'
                            : 'brand'
                        }
                      />
                    </div>
                  </td>
                  <td className="px-4 py-4 text-xs font-medium text-gray-600 whitespace-nowrap">
                    {project.deadline}
                  </td>
                  <td className="px-4 py-4 text-xs font-medium text-gray-800 whitespace-nowrap">
                    {formatINR(project.budget)}
                  </td>
                  <td className="px-4 py-4">
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        project.riskSummary?.riskLevel === 'HIGH'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : project.riskSummary?.riskLevel === 'MEDIUM'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      {project.riskSummary?.riskScore ?? 25}%
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right whitespace-nowrap">
                    {getStatusBadge(project.status)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
