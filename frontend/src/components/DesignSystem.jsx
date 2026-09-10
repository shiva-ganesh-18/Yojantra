import React from 'react';

/**
 * Modern Design System Button Component for Yojantra
 * Variants: primary, secondary, outline, ghost, danger, success, saffron
 * Sizes: sm, md, lg
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  loading = false,
  icon: Icon,
  iconPosition = 'left',
  onClick,
  type = 'button',
  fullWidth = false,
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-bold transition-all duration-150 rounded-xl focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98]';

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-xs sm:text-sm px-4 py-2.5 gap-2',
    lg: 'text-sm sm:text-base px-6 py-3.5 gap-2.5 rounded-2xl',
  };

  const variantStyles = {
    primary: 'bg-gov-navy-950 hover:bg-gov-navy-900 text-white shadow-sm hover:shadow focus:ring-gov-navy-900',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-800 focus:ring-slate-400',
    saffron: 'bg-gradient-to-r from-gov-saffron-600 to-gov-saffron-500 hover:from-gov-saffron-700 hover:to-gov-saffron-600 text-white shadow-md hover:shadow-lg focus:ring-gov-saffron-500',
    emerald: 'bg-gradient-to-r from-gov-emerald-600 to-gov-emerald-500 hover:from-gov-emerald-700 hover:to-gov-emerald-600 text-white shadow-md hover:shadow-lg focus:ring-gov-emerald-500',
    outline: 'border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 focus:ring-slate-400',
    ghost: 'bg-transparent hover:bg-slate-100 text-slate-700 focus:ring-slate-300',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles[size] || sizeStyles.md} ${variantStyles[variant] || variantStyles.primary} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : Icon && iconPosition === 'left' ? (
        <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} className="shrink-0" />
      ) : null}
      <span>{children}</span>
      {!loading && Icon && iconPosition === 'right' && (
        <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} className="shrink-0" />
      )}
    </button>
  );
}

/**
 * Reusable Status & Category Badges
 */
export function Badge({
  children,
  variant = 'default',
  size = 'md',
  icon: Icon,
  className = '',
  ...props
}) {
  const baseStyles = 'inline-flex items-center font-extrabold uppercase tracking-wider rounded-full select-none';

  const sizeStyles = {
    sm: 'text-[9px] px-2 py-0.5 gap-1',
    md: 'text-[10px] sm:text-[11px] px-2.5 py-1 gap-1.5',
    lg: 'text-xs px-3 py-1.5 gap-2',
  };

  const variantStyles = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200',
    primary: 'bg-gov-navy-100 text-gov-navy-900 border border-gov-navy-200',
    saffron: 'bg-gov-saffron-50 text-gov-saffron-800 border border-gov-saffron-200',
    emerald: 'bg-gov-emerald-50 text-gov-emerald-800 border border-gov-emerald-200',
    amber: 'bg-amber-50 text-amber-800 border border-amber-200',
    red: 'bg-red-50 text-red-700 border border-red-200',
    purple: 'bg-purple-50 text-purple-800 border border-purple-200',
    blue: 'bg-blue-50 text-blue-800 border border-blue-200',
  };

  return (
    <span
      className={`${baseStyles} ${sizeStyles[size] || sizeStyles.md} ${variantStyles[variant] || variantStyles.default} ${className}`}
      {...props}
    >
      {Icon && <Icon size={size === 'sm' ? 10 : 12} className="shrink-0" />}
      <span>{children}</span>
    </span>
  );
}

/**
 * Standard Surface Card with Consistent Border, Shadow & Radius
 */
export function Card({
  children,
  className = '',
  hoverEffect = false,
  onClick,
  ...props
}) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-gov ${
        hoverEffect ? 'transition-all duration-200 hover:shadow-gov-hover hover:border-slate-300' : ''
      } ${onClick ? 'cursor-pointer' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * Standard Form Input Component with Floating Label & Error Support
 */
export function Input({
  label,
  error,
  helperText,
  icon: Icon,
  className = '',
  containerClassName = '',
  required = false,
  ...props
}) {
  return (
    <div className={`space-y-1.5 text-left ${containerClassName}`}>
      {label && (
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
            <Icon size={16} />
          </div>
        )}
        <input
          className={`w-full rounded-xl border bg-slate-50 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-gov-navy-900/10 focus:border-gov-navy-950 disabled:opacity-60 disabled:bg-slate-100 ${
            Icon ? 'pl-10 pr-3.5' : 'px-3.5'
          } py-2.5 ${error ? 'border-red-400 focus:border-red-500 focus:ring-red-100' : 'border-slate-300'} ${className}`}
          {...props}
        />
      </div>
      {error && <p className="text-[11px] font-semibold text-red-600">{error}</p>}
      {!error && helperText && <p className="text-[11px] text-slate-500">{helperText}</p>}
    </div>
  );
}

/**
 * Standard Form Select Component
 */
export function Select({
  label,
  options = [],
  error,
  helperText,
  icon: Icon,
  className = '',
  containerClassName = '',
  required = false,
  children,
  ...props
}) {
  return (
    <div className={`space-y-1.5 text-left ${containerClassName}`}>
      {label && (
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
            <Icon size={16} />
          </div>
        )}
        <select
          className={`w-full rounded-xl border bg-slate-50 text-xs sm:text-sm text-slate-900 transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-gov-navy-900/10 focus:border-gov-navy-950 disabled:opacity-60 disabled:bg-slate-100 ${
            Icon ? 'pl-10 pr-8' : 'px-3.5 pr-8'
          } py-2.5 appearance-none ${error ? 'border-red-400' : 'border-slate-300'} ${className}`}
          {...props}
        >
          {children || options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      {error && <p className="text-[11px] font-semibold text-red-600">{error}</p>}
      {!error && helperText && <p className="text-[11px] text-slate-500">{helperText}</p>}
    </div>
  );
}

export default {
  Button,
  Badge,
  Card,
  Input,
  Select,
};
