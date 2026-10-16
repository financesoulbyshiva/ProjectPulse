import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  footer?: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  action,
  footer,
  padding = 'md',
  interactive = false,
  onClick,
}) => {
  const paddingMap = {
    none: 'p-0',
    sm: 'p-3',
    md: 'p-5',
    lg: 'p-6',
  };

  const interactiveClasses = interactive || onClick
    ? 'cursor-pointer motion-card-hover'
    : 'transition-all duration-200';

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg border border-gray-200 shadow-2xs ${interactiveClasses} ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3.5">
          <div>
            {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={paddingMap[padding]}>{children}</div>
      {footer && (
        <div className="border-t border-gray-100 bg-gray-50/50 px-5 py-3 rounded-b-lg">
          {footer}
        </div>
      )}
    </div>
  );
};
