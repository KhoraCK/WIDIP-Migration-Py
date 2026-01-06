import { Shield } from 'lucide-react';
import type { AccreditationLevel } from '../../types';
import { ACCREDITATION_LABELS, ACCREDITATION_DESCRIPTIONS, ACCREDITATION_COLORS } from '../../types';

interface LevelSelectorProps {
  value: AccreditationLevel;
  onChange: (level: AccreditationLevel) => void;
  disabled?: boolean;
  showDescription?: boolean;
  size?: 'sm' | 'md';
}

const LEVELS: AccreditationLevel[] = ['N0', 'N1', 'N2', 'N3', 'N4'];

export function LevelSelector({
  value,
  onChange,
  disabled = false,
  showDescription = true,
  size = 'md',
}: LevelSelectorProps) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {LEVELS.map((level) => (
          <button
            key={level}
            type="button"
            onClick={() => !disabled && onChange(level)}
            disabled={disabled}
            className={`
              flex items-center gap-1.5 rounded-lg transition-all
              ${size === 'sm' ? 'px-2 py-1 text-xs' : 'px-3 py-2 text-sm'}
              ${value === level
                ? `${ACCREDITATION_COLORS[level]} ring-2 ring-offset-2 ring-offset-bg-secondary ring-current`
                : 'bg-bg-primary text-text-secondary hover:bg-bg-secondary'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <Shield className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
            <span className="font-medium">{level}</span>
            {size !== 'sm' && (
              <span className="hidden sm:inline">- {ACCREDITATION_LABELS[level]}</span>
            )}
          </button>
        ))}
      </div>
      {showDescription && (
        <p className="text-xs text-text-secondary">
          {ACCREDITATION_DESCRIPTIONS[value]}
        </p>
      )}
    </div>
  );
}

// Badge affichant le niveau (pour la liste des utilisateurs)
interface LevelBadgeProps {
  level: AccreditationLevel;
  size?: 'sm' | 'md';
}

export function LevelBadge({ level, size = 'md' }: LevelBadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        ${size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-xs'}
        ${ACCREDITATION_COLORS[level]}
      `}
      title={ACCREDITATION_DESCRIPTIONS[level]}
    >
      <Shield className={size === 'sm' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />
      {level}
    </span>
  );
}
