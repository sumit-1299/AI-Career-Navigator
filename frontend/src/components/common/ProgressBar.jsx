import React from 'react';

export function ProgressBar({
  value = 0,
  max = 100,
  color = 'bg-primary-600',
  className = '',
}) {
  const percentage = Math.min(100, Math.max(0, Math.round((value / (max || 1)) * 100)));

  return (
    <div className={`w-full bg-slate-100 rounded-full h-2.5 overflow-hidden ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
