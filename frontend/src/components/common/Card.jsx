import React from 'react';

export function Card({
  children,
  className = '',
  interactive = false,
  onClick,
  ...props
}) {
  const baseClass = interactive
    ? 'card-interactive cursor-pointer'
    : 'card-standard';

  return (
    <div
      className={`${baseClass} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  subtext,
  icon: Icon,
  trend,
  className = '',
}) {
  return (
    <Card className={`p-5 flex flex-col justify-between ${className}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          {label}
        </span>
        {Icon && (
          <div className="p-2 rounded-xl bg-slate-50 text-slate-500 border border-slate-100">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="mt-3">
        <div className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">
          {value}
        </div>
        {(subtext || trend) && (
          <div className="flex items-center gap-2 mt-1">
            {trend && (
              <span
                className={`text-xs font-bold ${
                  trend.positive ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {trend.positive ? '↑' : '↓'} {trend.label}
              </span>
            )}
            {subtext && <span className="text-xs text-slate-400">{subtext}</span>}
          </div>
        )}
      </div>
    </Card>
  );
}

export function InsightCard({
  title,
  subtitle,
  children,
  badge,
  action,
  className = '',
}) {
  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {badge}
            <h3 className="font-bold text-base text-slate-900 tracking-tight">{title}</h3>
          </div>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      <div>{children}</div>
    </Card>
  );
}

export default Card;
