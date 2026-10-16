import React from 'react';
import type { RiskLevel } from '../../types';
import { useAnimatedNumber } from '../../hooks/useAnimatedNumber';

interface RiskGaugeProps {
  score: number; // 0 - 100
  level: RiskLevel;
  delayProbability?: number;
  expectedDelay?: string;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  level,
  delayProbability,
  expectedDelay,
  size = 'md',
  showDetails = true,
}) => {
  const clampedScore = Math.min(100, Math.max(0, score));

  // Animated numerical score (0 -> actual value)
  const animatedScore = useAnimatedNumber(clampedScore, {
    duration: 700,
    decimals: 0,
    startFromZero: true,
  });
  const animatedDelayProb = useAnimatedNumber(delayProbability || 0, {
    duration: 650,
    decimals: 0,
    startFromZero: true,
  });

  // Status-aware semantic colors
  const getColor = () => {
    if (level === 'HIGH' || clampedScore >= 70) return '#dc2626'; // rose-600
    if (level === 'MEDIUM' || clampedScore >= 40) return '#d97706'; // amber-600
    return '#16a34a'; // emerald-600
  };

  const getBadgeStyle = () => {
    if (level === 'HIGH' || clampedScore >= 70) {
      return {
        classes: 'text-rose-700 bg-rose-50 border-rose-200',
        label: 'HIGH RISK • At Risk',
      };
    }
    if (level === 'MEDIUM' || clampedScore >= 40) {
      return {
        classes: 'text-amber-700 bg-amber-50 border-amber-200',
        label: 'MEDIUM RISK • Needs Attention',
      };
    }
    return {
      classes: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      label: 'LOW RISK • On Track',
    };
  };

  const badge = getBadgeStyle();

  // Semi-circle SVG coordinates: radius 40, circumference = pi * 40 ≈ 125.66
  // Driven smoothly in lockstep with the numerical score
  const strokeDashoffset = 125.66 - (animatedScore / 100) * 125.66;

  const sizeClasses = {
    sm: 'w-32',
    md: 'w-44',
    lg: 'w-56',
  };

  return (
    <div className="flex flex-col items-center text-center select-none">
      <div className={`relative ${sizeClasses[size]}`}>
        <svg viewBox="0 0 100 55" className="w-full overflow-visible">
          {/* Background Arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#f1f5f9"
            strokeWidth="9"
            strokeLinecap="round"
          />
          {/* Active Progress Arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke={getColor()}
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray="125.66"
            strokeDashoffset={strokeDashoffset}
            style={{
              transition: 'stroke 300ms ease',
            }}
          />
        </svg>

        {/* Center Numerical Score */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1 pointer-events-none">
          <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-gray-900 leading-none tabular-nums font-mono">
            {Math.round(animatedScore)}%
          </span>
          <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider mt-1">
            Risk Score
          </span>
        </div>
      </div>

      {/* Semantic Risk Badge with Fade + Slight Upward Movement */}
      <div className="mt-3.5 animate-slide-up stagger-2">
        <span
          className={`inline-flex items-center px-3 py-0.5 rounded-full text-[11px] font-bold border transition-colors duration-300 ${badge.classes}`}
        >
          {badge.label}
        </span>
      </div>

      {/* Supporting Key Telemetry Metrics — Staggered Reveal */}
      {showDetails && (
        <div className="mt-4 grid grid-cols-2 gap-3 w-full border-t border-gray-100 pt-3 text-xs animate-slide-up stagger-3">
          {delayProbability !== undefined && (
            <div className="p-1.5 rounded-md bg-gray-50/75 border border-gray-100">
              <span className="text-gray-400 text-[10px] font-semibold uppercase tracking-wider block">Delay Probability</span>
              <span className="font-bold text-gray-900 text-sm mt-0.5 block tabular-nums">
                {Math.round(animatedDelayProb)}%
              </span>
            </div>
          )}
          {expectedDelay && (
            <div className="p-1.5 rounded-md bg-gray-50/75 border border-gray-100">
              <span className="text-gray-400 text-[10px] font-semibold uppercase tracking-wider block">Expected Slip</span>
              <span className="font-bold text-gray-900 text-sm mt-0.5 block">
                {expectedDelay}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
