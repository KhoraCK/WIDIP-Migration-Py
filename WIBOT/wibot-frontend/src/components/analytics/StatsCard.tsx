import type { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  progress?: number; // 0-100
}

const colorClasses = {
  blue: 'text-blue-400 bg-blue-500/10',
  green: 'text-green-400 bg-green-500/10',
  orange: 'text-orange-400 bg-orange-500/10',
  purple: 'text-purple-400 bg-purple-500/10',
  red: 'text-red-400 bg-red-500/10',
};

const progressColors = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  orange: 'bg-orange-500',
  purple: 'bg-purple-500',
  red: 'bg-red-500',
};

export function StatsCard({ title, value, subtitle, icon: Icon, color = 'blue', progress }: StatsCardProps) {
  return (
    <div className="bg-bg-secondary border border-border rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-text-secondary font-medium">{title}</p>
          <p className="text-2xl font-bold text-text-primary mt-1">
            {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
          </p>
          {subtitle && (
            <p className="text-xs text-text-secondary mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      {progress !== undefined && (
        <div className="mt-4">
          <div className="w-full h-2 bg-bg-primary rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${progressColors[color]}`}
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
