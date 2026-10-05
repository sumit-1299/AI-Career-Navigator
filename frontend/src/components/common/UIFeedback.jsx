import React from 'react';
import { Loader2, AlertCircle, CheckCircle2, Info } from 'lucide-react';

export function Spinner({ size = 'md', className = '' }) {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-10 h-10',
  };

  return (
    <Loader2
      className={`animate-spin text-primary-600 ${sizeMap[size] || sizeMap.md} ${className}`}
    />
  );
}

export function Alert({ type = 'info', message, className = '' }) {
  if (!message) return null;

  const styles = {
    info: {
      bg: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: Info,
      iconColor: 'text-blue-500',
    },
    success: {
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
      icon: CheckCircle2,
      iconColor: 'text-emerald-500',
    },
    error: {
      bg: 'bg-rose-50 border-rose-200 text-rose-800',
      icon: AlertCircle,
      iconColor: 'text-rose-500',
    },
  };

  const current = styles[type] || styles.info;
  const Icon = current.icon;

  return (
    <div
      className={`p-4 rounded-xl border flex items-start gap-3 text-sm ${current.bg} ${className}`}
    >
      <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${current.iconColor}`} />
      <span className="leading-relaxed">{message}</span>
    </div>
  );
}
