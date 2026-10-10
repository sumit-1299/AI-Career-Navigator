import React from 'react';
import { Badge } from './Badge';

export function SectionHeader({
  badge,
  title,
  subtitle,
  action,
  className = '',
}) {
  return (
    <div className={`bg-white rounded-2xl p-6 md:p-8 shadow-card border border-slate-200/90 ${className}`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          {badge && (
            <div className="mb-2">
              <Badge variant="primary" size="sm" dot>
                {badge}
              </Badge>
            </div>
          )}
          <h1 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-slate-500 text-sm mt-1.5 leading-relaxed max-w-3xl">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="flex items-center gap-3 shrink-0">{action}</div>}
      </div>
    </div>
  );
}

export default SectionHeader;
