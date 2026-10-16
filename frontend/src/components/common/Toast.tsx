import React from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useProject();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full px-4 sm:px-0 pointer-events-none">
      {toasts.map((toast) => {
        const iconMap = {
          success: <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />,
          error: <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />,
          info: <Info className="h-4 w-4 text-blue-600 shrink-0" />,
        };

        const borderMap = {
          success: 'border-emerald-200/80 bg-white shadow-md text-gray-900',
          error: 'border-rose-200/80 bg-white shadow-md text-gray-900',
          info: 'border-blue-200/80 bg-white shadow-md text-gray-900',
        };

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-center justify-between p-3.5 rounded-lg border text-xs font-medium animate-toast ${borderMap[toast.type]}`}
            style={{
              boxShadow: '0 8px 24px -4px rgba(0, 0, 0, 0.08), 0 2px 6px -1px rgba(0, 0, 0, 0.04)',
            }}
          >
            <div className="flex items-center gap-2.5">
              {iconMap[toast.type]}
              <span>{toast.message}</span>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-gray-400 hover:text-gray-600 ml-2 p-0.5 rounded motion-press"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
