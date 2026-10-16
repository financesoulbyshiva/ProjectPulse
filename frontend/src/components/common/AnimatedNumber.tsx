import React from 'react';
import { useAnimatedNumber } from '../../hooks/useAnimatedNumber';

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  startFromZero?: boolean;
  formatter?: (val: number) => string;
  className?: string;
}

export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  duration = 550,
  decimals = 0,
  prefix = '',
  suffix = '',
  startFromZero = false,
  formatter,
  className = '',
}) => {
  const animated = useAnimatedNumber(value, { duration, decimals, startFromZero });

  const formatted = formatter
    ? formatter(animated)
    : `${prefix}${decimals > 0 ? animated.toFixed(decimals) : Math.round(animated)}${suffix}`;

  return <span className={className}>{formatted}</span>;
};
