import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import type { ProjectStatus } from '../types';

export const CreateProjectPage: React.FC = () => {
  const { addProject, teamMembers } = useProject();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState('2026-10-15');
  const [deadline, setDeadline] = useState('2026-12-15');
  const [budget, setBudget] = useState('100000');
  const [manager, setManager] = useState(teamMembers[0]?.name || '');
  const [selectedMembers, setSelectedMembers] = useState<string[]>(() =>
    teamMembers.slice(0, 3).map((tm) => tm.name)
  );

  useEffect(() => {
    if (!manager && teamMembers.length > 0) {
      setManager(teamMembers[0].name);
    }
    if (selectedMembers.length === 0 && teamMembers.length > 0) {
      setSelectedMembers(teamMembers.slice(0, 3).map((tm) => tm.name));
    }
  }, [teamMembers, manager, selectedMembers.length]);
  const [complexity, setComplexity] = useState<'Low' | 'Medium' | 'High'>('Medium');
  const [dependencies, setDependencies] = useState('2');
  const [status, setStatus] = useState<ProjectStatus>('On Track');

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const toggleMember = (mName: string) => {
    setSelectedMembers((prev) =>
      prev.includes(mName) ? prev.filter((m) => m !== mName) : [...prev, mName]
    );
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = 'Project name is required.';
    if (!description.trim()) errs.description = 'Description is required.';
    if (!startDate) errs.startDate = 'Start date is required.';
    if (!deadline) errs.deadline = 'Target deadline is required.';
    else if (new Date(deadline) <= new Date(startDate)) {
      errs.deadline = 'Deadline must be after start date.';
    }
    const numBudget = Number(budget);
    if (!budget || isNaN(numBudget) || numBudget <= 0) {
      errs.budget = 'Please enter a valid positive budget amount.';
    }
    if (selectedMembers.length === 0) {
      errs.members = 'Select at least one team member.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    await new Promise((r) => setTimeout(r, 500));

    const created = await addProject({
      name,
      description,
      manager,
      startDate,
      deadline,
      budget: Number(budget),
      status,
      teamSize: selectedMembers.length,
      teamMembers: selectedMembers,
      complexity,
      dependencies: Number(dependencies) || 0,
    });

    setIsSubmitting(false);
    setIsSuccess(true);

    setTimeout(() => {
      navigate(`/projects/${created.id}`);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/projects')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Projects
        </button>
      </div>

      <Card
        title="Initialize New Project"
        subtitle="Configure project parameters, budget allocation, and assigned engineering team."
      >
        {isSuccess ? (
          <div className="py-12 text-center space-y-3">
            <CheckCircle2 className="h-12 w-12 text-emerald-600 mx-auto" />
            <h3 className="text-base font-semibold text-gray-900">Project Created Successfully!</h3>
            <p className="text-xs text-gray-500">
              Initializing ML feature telemetry and redirecting to project details...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6 pt-2">
            {/* 2-Column Desktop Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Left Column */}
              <div className="space-y-4">
                <Input
                  label="Project Name"
                  placeholder="e.g., Cloud ERP Migration"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  error={errors.name}
                  required
                />

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Description <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Brief description of project deliverables and objective..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className={`block w-full rounded-md border text-sm py-2 px-3 focus:outline-none ${
                      errors.description
                        ? 'border-red-300 text-red-900 focus:border-red-500'
                        : 'border-gray-300 text-gray-900 focus:border-blue-500'
                    }`}
                  />
                  {errors.description && (
                    <p className="mt-1 text-xs text-red-600">{errors.description}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Start Date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    error={errors.startDate}
                    required
                  />
                  <Input
                    label="Target Deadline"
                    type="date"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    error={errors.deadline}
                    required
                  />
                </div>

                <Input
                  label="Total Budget (INR ₹)"
                  type="number"
                  placeholder="100000"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  error={errors.budget}
                  helperText="Initial financial allocation in rupees"
                  required
                />
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                <Select
                  label="Project Manager"
                  value={manager}
                  onChange={(e) => setManager(e.target.value)}
                  options={teamMembers.map((tm) => ({
                    value: tm.name,
                    label: `${tm.name} (${tm.role})`,
                  }))}
                />

                <div className="grid grid-cols-2 gap-3">
                  <Select
                    label="Task Complexity"
                    value={complexity}
                    onChange={(e) => setComplexity(e.target.value as 'Low' | 'Medium' | 'High')}
                    options={[
                      { value: 'Low', label: 'Low (Score 1.0)' },
                      { value: 'Medium', label: 'Medium (Score 2.0)' },
                      { value: 'High', label: 'High (Score 3.0)' },
                    ]}
                  />

                  <Input
                    label="Dependencies Count"
                    type="number"
                    min="0"
                    value={dependencies}
                    onChange={(e) => setDependencies(e.target.value)}
                    helperText="Predecessor blocker links"
                  />
                </div>

                <Select
                  label="Initial Health Status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as ProjectStatus)}
                  options={[
                    { value: 'On Track', label: 'On Track' },
                    { value: 'At Risk', label: 'At Risk' },
                  ]}
                />

                {/* Team Members Multi-select */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Assign Team Members <span className="text-red-500">*</span>
                  </label>
                  <div className="max-h-36 overflow-y-auto rounded-md border border-gray-200 p-2 space-y-1.5 bg-gray-50/50">
                    {teamMembers.map((tm) => {
                      const isSelected = selectedMembers.includes(tm.name);
                      return (
                        <label
                          key={tm.id}
                          className={`flex items-center justify-between p-1.5 rounded cursor-pointer text-xs transition-colors ${
                            isSelected ? 'bg-blue-50 text-blue-900 font-medium' : 'hover:bg-white text-gray-700'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleMember(tm.name)}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span>{tm.name}</span>
                          </div>
                          <span className="text-[10px] text-gray-400">{tm.role}</span>
                        </label>
                      );
                    })}
                  </div>
                  {errors.members && (
                    <p className="mt-1 text-xs text-red-600">{errors.members}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/projects')}
              >
                Cancel
              </Button>
              <Button type="submit" isLoading={isSubmitting}>
                Create Project
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
};
