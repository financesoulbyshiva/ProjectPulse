import { useState, useEffect, useRef } from 'react';
import { useReducedMotion } from './useReducedMotion';

interface UseAnimatedNumberOptions {
  duration?: number; // duration in ms, default 550ms
  decimals?: number; // decimal places, default 0
  startFromZero?: boolean; // if true, counts up from 0 on initial mount
}

/**
 * Hook for smooth numerical transitions (Linear/Vercel/Stripe style).
 * Uses requestAnimationFrame with cubic ease-out deceleration.
 * Respects prefers-reduced-motion accessibility preference.
 */
export function useAnimatedNumber(
  targetValue: number,
  options: UseAnimatedNumberOptions = {}
): number {
  const { duration = 550, decimals = 0, startFromZero = false } = options;
  const prefersReduced = useReducedMotion();

  const [displayValue, setDisplayValue] = useState<number>(() =>
    prefersReduced || !startFromZero ? targetValue : 0
  );
  const prevValueRef = useRef<number>(
    prefersReduced || !startFromZero ? targetValue : 0
  );
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    // If user prefers reduced motion or duration is 0, update immediately
    if (prefersReduced || duration <= 0) {
      setDisplayValue(targetValue);
      prevValueRef.current = targetValue;
      return;
    }

    const startValue = prevValueRef.current;
    const diff = targetValue - startValue;

    // Skip animation if difference is negligible
    if (Math.abs(diff) < 0.0001) {
      setDisplayValue(targetValue);
      return;
    }

    let startTime: number | null = null;

    // Cubic ease-out curve: fast start, soft settle
    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

    const step = (now: number) => {
      if (startTime === null) startTime = now;
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutCubic(progress);

      const current = startValue + diff * easedProgress;
      const factor = Math.pow(10, decimals);
      const rounded = Math.round(current * factor) / factor;

      setDisplayValue(rounded);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      } else {
        setDisplayValue(targetValue);
        prevValueRef.current = targetValue;
      }
    };

    frameRef.current = requestAnimationFrame(step);

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [targetValue, duration, decimals, prefersReduced]);

  return displayValue;
}
