import React from 'react';

export function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
  dot = false,
}) {
  const variantStyles = {
    default: 'bg-slate-100 text-slate-700 border-slate-200/80',
    primary: 'bg-primary-50 text-primary-700 border-primary-200/80',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    warning: 'bg-amber-50 text-amber-700 border-amber-200/80',
    error: 'bg-rose-50 text-rose-700 border-rose-200/80',
    info: 'bg-blue-50 text-blue-700 border-blue-200/80',
    purple: 'bg-purple-50 text-purple-700 border-purple-200/80',
  };

  const dotStyles = {
    default: 'bg-slate-400',
    primary: 'bg-primary-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    error: 'bg-rose-500',
    info: 'bg-blue-500',
    purple: 'bg-purple-500',
  };

  const sizeStyles = {
    xs: 'text-[10px] px-2 py-0.5 font-semibold',
    sm: 'text-xs px-2.5 py-0.5 font-semibold',
    md: 'text-xs px-3 py-1 font-bold',
    lg: 'text-sm px-3.5 py-1.5 font-bold',
  };

  const currentVariant = variantStyles[variant] || variantStyles.default;
  const currentSize = sizeStyles[size] || sizeStyles.sm;
  const currentDot = dotStyles[variant] || dotStyles.default;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border tracking-wide transition-colors ${currentVariant} ${currentSize} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${currentDot}`} />}
      {children}
    </span>
  );
}

export default Badge;
