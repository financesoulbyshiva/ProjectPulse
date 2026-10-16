import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ToastContainer } from '../common/Toast';

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Map route to page title and subtitle
  const getHeaderMeta = () => {
    const path = location.pathname;
    if (path === '/' || path === '/dashboard') {
      return {
        title: 'Dashboard',
        subtitle: 'Project overview and current performance.',
      };
    }
    if (path === '/projects') {
      return {
        title: 'Projects',
        subtitle: 'Manage and monitor all company projects.',
      };
    }
    if (path === '/projects/create') {
      return {
        title: 'Create Project',
        subtitle: 'Initialize a new project with budget and milestones.',
      };
    }
    if (path.startsWith('/projects/')) {
      return {
        title: 'Project Details',
        subtitle: 'Project specifications, tasks, team, and risk overview.',
      };
    }
    if (path === '/tasks') {
      return {
        title: 'Tasks',
        subtitle: 'Track work items, assignees, priorities, and deadlines.',
      };
    }
    if (path === '/team') {
      return {
        title: 'Team',
        subtitle: 'Team roster, allocations, and workload balancing.',
      };
    }
    if (path === '/analytics') {
      return {
        title: 'Analytics',
        subtitle: 'Understand project performance through data.',
      };
    }
    if (path === '/risk-analysis') {
      return {
        title: 'AI Risk Analysis',
        subtitle: 'Machine learning project delay forecasting and recommendations.',
      };
    }
    if (path === '/prediction-details') {
      return {
        title: 'Prediction Details',
        subtitle: 'Technical ML feature breakdown and model specifications.',
      };
    }
    if (path === '/settings') {
      return {
        title: 'Settings',
        subtitle: 'Account preferences, notifications, and profile details.',
      };
    }
    return {
      title: 'ProjectPulse',
      subtitle: 'Track. Analyze. Predict. Deliver.',
    };
  };

  const { title, subtitle } = getHeaderMeta();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Header
          title={title}
          subtitle={subtitle}
          onOpenSidebar={() => setSidebarOpen(true)}
        />
        <main className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl w-full mx-auto">
          <div key={location.pathname} className="spatial-page-enter">
            <Outlet />
          </div>
        </main>
      </div>

      <ToastContainer />
    </div>
  );
};
