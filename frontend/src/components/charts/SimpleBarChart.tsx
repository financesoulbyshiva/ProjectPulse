import React, { useState, useEffect } from 'react';
import { useReducedMotion } from '../../hooks/useReducedMotion';

interface BarItem {
  label: string;
  value: number; // 0 - 100 or actual unit
  displayValue?: string;
  color?: string; // hex or tailwind class
}

interface SimpleBarChartProps {
  items: BarItem[];
  maxValue?: number;
  height?: number;
  unit?: string;
}

export const SimpleBarChart: React.FC<SimpleBarChartProps> = ({
  items,
  maxValue,
  unit = '%',
}) => {
  const prefersReduced = useReducedMotion();
  const [mounted, setMounted] = useState(prefersReduced);

  useEffect(() => {
    if (!prefersReduced) {
      const timer = setTimeout(() => setMounted(true), 40);
      return () => clearTimeout(timer);
    }
  }, [prefersReduced]);

  const calculatedMax = maxValue || Math.max(...items.map((i) => i.value), 100);

  return (
    <div className="w-full space-y-3.5 py-1">
      {items.map((item, idx) => {
        const percentage = Math.min(100, Math.max(0, (item.value / calculatedMax) * 100));
        const currentWidth = mounted ? percentage : 0;

        return (
          <div key={idx} className="space-y-1 group">
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-gray-700 truncate max-w-[200px] transition-colors group-hover:text-gray-900">
                {item.label}
              </span>
              <span className="font-semibold text-gray-900 tabular-nums">
                {item.displayValue || `${item.value}${unit}`}
              </span>
            </div>
            <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${item.color || 'bg-blue-600'}`}
                style={{
                  width: `${currentWidth}%`,
                  transition: prefersReduced
                    ? 'none'
                    : `width 650ms cubic-bezier(0.16, 1, 0.3, 1) ${idx * 60}ms`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
