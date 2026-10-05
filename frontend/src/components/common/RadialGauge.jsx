import React from 'react';

export function RadialGauge({
  score = 0,
  size = 140,
  strokeWidth = 12,
  label = 'Readiness',
}) {
  const normalizedScore = Math.min(100, Math.max(0, Math.round(score)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let color = '#6366f1'; // indigo
  if (normalizedScore >= 80) color = '#10b981'; // emerald
  else if (normalizedScore >= 60) color = '#3b82f6'; // blue
  else if (normalizedScore >= 30) color = '#f59e0b'; // amber
  else color = '#ef4444'; // rose

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#f1f5f9"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-black text-slate-800 tracking-tight leading-none">
          {normalizedScore}%
        </span>
        {label && (
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
