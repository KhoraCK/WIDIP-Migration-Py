import type { SpinnerProps } from '../../types';

const sizeStyles: Record<string, string> = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return (
    <div
      className={`
        inline-block
        border-2 border-text-secondary border-t-accent
        rounded-full
        animate-spin
        ${sizeStyles[size]}
        ${className}
      `}
      role="status"
      aria-label="Chargement..."
    >
      <span className="sr-only">Chargement...</span>
    </div>
  );
}
