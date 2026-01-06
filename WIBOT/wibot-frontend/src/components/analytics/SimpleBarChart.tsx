interface DataPoint {
  label: string;
  value: number;
}

interface SimpleBarChartProps {
  data: DataPoint[];
  title: string;
  color?: string;
  height?: number;
}

export function SimpleBarChart({ data, title, color = '#6366f1', height = 200 }: SimpleBarChartProps) {
  const maxValue = Math.max(...data.map(d => d.value), 1);

  return (
    <div className="bg-bg-secondary border border-border rounded-xl p-5">
      <h3 className="text-sm font-medium text-text-secondary mb-4">{title}</h3>
      <div className="flex items-end gap-1" style={{ height }}>
        {data.map((point, index) => {
          const barHeight = (point.value / maxValue) * 100;
          return (
            <div key={index} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-xs text-text-secondary">{point.value}</span>
              <div
                className="w-full rounded-t transition-all duration-300 hover:opacity-80"
                style={{
                  height: `${barHeight}%`,
                  backgroundColor: color,
                  minHeight: point.value > 0 ? '4px' : '0'
                }}
                title={`${point.label}: ${point.value}`}
              />
              <span className="text-xs text-text-secondary truncate w-full text-center">
                {point.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
