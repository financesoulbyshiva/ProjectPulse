import React, { useState } from 'react';
import { Plus, UserPlus, Users, AlertCircle } from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import type { WorkloadLevel } from '../types';

export const TeamPage: React.FC = () => {
  const { teamMembers, addTeamMember } = useProject();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Full Stack Engineer');
  const [capacity, setCapacity] = useState('40');
  const [workload, setWorkload] = useState<WorkloadLevel>('Medium');

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;

    await addTeamMember({
      name,
      email,
      role,
      workload,
      status: 'Active',
      capacityHours: Number(capacity) || 40,
    });

    setIsModalOpen(false);
    setName('');
    setEmail('');
  };

  const getWorkloadBadge = (wl: WorkloadLevel) => {
    switch (wl) {
      case 'High':
        return <Badge variant="danger" dot>High Load</Badge>;
      case 'Medium':
        return <Badge variant="warning" dot>Medium Load</Badge>;
      case 'Low':
        return <Badge variant="success" dot>Low Load</Badge>;
    }
  };

  const overloadedCount = teamMembers.filter((m) => m.workload === 'High').length;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Top Banner & Action */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Users className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-gray-900">Engineering Roster</h2>
            <p className="text-xs text-gray-500">
              {teamMembers.length} active contributors • {overloadedCount} overloaded
            </p>
          </div>
        </div>

        <Button onClick={() => setIsModalOpen(true)} icon={<Plus className="h-4 w-4" />}>
          Add Member
        </Button>
      </div>

      {overloadedCount > 0 && (
        <div className="flex items-center gap-2.5 p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800">
          <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
          <span>
            <strong>Resource Balancing Alert:</strong> {overloadedCount} team members have high assigned workloads. Consider task redistribution to mitigate delay risks.
          </span>
        </div>
      )}

      {/* Team Members Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-2xs">
        <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
          <thead className="bg-gray-50/75">
            <tr className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              <th className="px-5 py-3.5">Member</th>
              <th className="px-4 py-3.5">Role</th>
              <th className="px-4 py-3.5 text-center">Active Projects</th>
              <th className="px-4 py-3.5 text-center">Assigned Tasks</th>
              <th className="px-4 py-3.5 text-center">Completed Tasks</th>
              <th className="px-4 py-3.5">Workload</th>
              <th className="px-5 py-3.5 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {teamMembers.map((member) => (
              <tr key={member.id} className="hover:bg-gray-50/75 transition-colors">
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs shrink-0">
                      {member.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900 block">{member.name}</span>
                      <span className="text-xs text-gray-500 block">{member.email}</span>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 text-xs font-medium text-gray-700 whitespace-nowrap">
                  {member.role}
                </td>
                <td className="px-4 py-4 text-xs font-semibold text-gray-800 text-center whitespace-nowrap">
                  {member.activeProjects}
                </td>
                <td className="px-4 py-4 text-xs font-semibold text-gray-800 text-center whitespace-nowrap">
                  {member.assignedTasks}
                </td>
                <td className="px-4 py-4 text-xs font-semibold text-emerald-700 text-center whitespace-nowrap">
                  {member.completedTasks}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  {getWorkloadBadge(member.workload)}
                </td>
                <td className="px-5 py-4 text-right whitespace-nowrap">
                  <Badge variant={member.status === 'Active' ? 'success' : 'neutral'} size="sm">
                    {member.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Member Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Team Member"
        description="Register a new contributor to the project workspace"
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="e.g. Ananya Rao"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="Enter your email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Input
            label="Role Title"
            placeholder="e.g. Senior Backend Engineer"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Weekly Capacity (Hours)"
              type="number"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              helperText="Standard is 40 hrs/week"
              required
            />

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Initial Workload
              </label>
              <select
                value={workload}
                onChange={(e) => setWorkload(e.target.value as WorkloadLevel)}
                className="w-full text-xs p-2 rounded-md border border-gray-300 bg-white"
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" icon={<UserPlus className="h-4 w-4" />}>
              Add Contributor
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
