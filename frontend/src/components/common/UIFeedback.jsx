import React from 'react';
import { Loader2, AlertCircle, CheckCircle2, Info, XCircle, AlertTriangle, X } from 'lucide-react';

export function Spinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-10 h-10',
  };

  return (
    <Loader2
      className={`animate-spin text-primary-600 ${sizes[size] || sizes.md} ${className}`}
    />
  );
}

export function Alert({
  type = 'info',
  title,
  message,
  children,
  onClose,
  className = '',
}) {
  const types = {
    info: {
      container: 'bg-blue-50/70 border-blue-200/80 text-blue-900',
      icon: <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />,
    },
    success: {
      container: 'bg-emerald-50/70 border-emerald-200/80 text-emerald-900',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />,
    },
    warning: {
      container: 'bg-amber-50/70 border-amber-200/80 text-amber-900',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />,
    },
    error: {
      container: 'bg-rose-50/70 border-rose-200/80 text-rose-900',
      icon: <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />,
    },
  };

  const current = types[type] || types.info;

  return (
    <div
      className={`p-4 rounded-xl border flex items-start gap-3 relative shadow-subtle ${current.container} ${className}`}
      role="alert"
    >
      {current.icon}
      <div className="flex-1 text-sm">
        {title && <h5 className="font-bold text-sm mb-1 leading-tight">{title}</h5>}
        {message && <p className="leading-relaxed">{message}</p>}
        {children}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/40 transition"
          aria-label="Dismiss alert"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  icon: Icon = Info,
  title = 'No items found',
  message = 'There is currently no data matching your query or filter parameters.',
  action,
  className = '',
}) {
  return (
    <div className={`bg-white rounded-2xl p-12 text-center border border-slate-200/90 shadow-card ${className}`}>
      <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400 shadow-subtle">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-500 mt-1.5 max-w-sm mx-auto leading-relaxed">{message}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = 'Failed to load data',
  message = 'An unexpected error occurred while communicating with the server.',
  onRetry,
  className = '',
}) {
  return (
    <div className={`bg-rose-50/40 rounded-2xl p-8 text-center border border-rose-200/80 shadow-subtle ${className}`}>
      <div className="w-12 h-12 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center mx-auto mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl shadow-subtle transition"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse bg-slate-200/80 rounded-lg ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-card space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="w-1/3 h-5" />
        <Skeleton className="w-16 h-5 rounded-full" />
      </div>
      <Skeleton className="w-full h-12" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="w-20 h-6 rounded-md" />
        <Skeleton className="w-20 h-6 rounded-md" />
      </div>
    </div>
  );
}
