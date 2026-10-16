import React from 'react';
import { useAnimatedNumber } from '../../hooks/useAnimatedNumber';

interface ProgressProps {
  value: number; // 0 - 100
  size?: 'sm' | 'md' | 'lg';
  variant?: 'brand' | 'success' | 'warning' | 'danger';
  showLabel?: boolean;
  className?: string;
  animate?: boolean;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  size = 'md',
  variant = 'brand',
  showLabel = false,
  className = '',
  animate = true,
}) => {
  const clamped = Math.min(100, Math.max(0, value));
  const animatedValue = useAnimatedNumber(animate ? clamped : clamped, { duration: 600, decimals: 0 });

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  const variantClasses = {
    brand: 'bg-blue-600',
    success: 'bg-emerald-600',
    warning: 'bg-amber-500',
    danger: 'bg-rose-600',
  };

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between items-center mb-1 text-xs">
          <span className="font-medium text-gray-700">Progress</span>
          <span className="font-semibold text-gray-900 tabular-nums">
            {Math.round(animatedValue)}%
          </span>
        </div>
      )}
      <div className={`w-full bg-gray-100 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`h-full rounded-full ${variantClasses[variant]}`}
          style={{
            width: `${animatedValue}%`,
            transition: 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      </div>
    </div>
  );
};
