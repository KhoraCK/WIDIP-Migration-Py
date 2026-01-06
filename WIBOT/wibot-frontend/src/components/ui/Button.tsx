import { Loader2 } from 'lucide-react';
import type { ButtonProps } from '../../types';

const variantStyles: Record<string, string> = {
  primary: 'bg-accent hover:bg-accent-hover text-white',
  secondary: 'bg-bg-secondary hover:bg-bg-user-msg text-text-primary border border-border',
  ghost: 'bg-transparent hover:bg-bg-secondary text-text-primary',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
};

const sizeStyles: Record<string, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
};

export function Button({
  variant = 'primary',
  size = 'md',
  onClick,
  children,
  disabled = false,
  loading = false,
  type = 'button',
  className = '',
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center gap-2
        font-medium rounded-lg
        transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-bg-primary
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}
