import React from 'react';

export function RadialGauge({
  score = 0,
  size = 140,
  strokeWidth = 10,
  label = 'Fit Score',
  subtext = '',
  colorClass = 'text-primary-600',
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.min(100, Math.max(0, Math.round(score)));
  const offset = circumference - (clampedScore / 100) * circumference;

  return (
    <div
      className="flex flex-col items-center justify-center relative select-none"
      role="progressbar"
      aria-valuenow={clampedScore}
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="w-full h-full -rotate-90 transform" viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className="text-slate-100 stroke-current"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress stroke */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className={`${colorClass} stroke-current transition-all duration-700 ease-out`}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            fill="transparent"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">
            {clampedScore}%
          </span>
          {label && (
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">
              {label}
            </span>
          )}
        </div>
      </div>
      {subtext && <p className="text-xs text-slate-500 mt-2 font-medium">{subtext}</p>}
    </div>
  );
}

export default RadialGauge;
