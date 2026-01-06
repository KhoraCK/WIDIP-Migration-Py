import type { InputProps } from '../../types';

export function Input({
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  disabled = false,
  className = '',
  id,
  name,
}: InputProps) {
  return (
    <div className="w-full">
      <input
        type={type}
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          w-full px-4 py-3
          bg-bg-secondary text-text-primary
          border rounded-lg
          placeholder:text-text-secondary
          transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
          ${error ? 'border-red-500' : 'border-border'}
          ${className}
        `}
      />
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
