interface DataSegment {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: DataSegment[];
  title: string;
  size?: number;
}

export function DonutChart({ data, title, size = 160 }: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  // Calculate stroke-dasharray for each segment
  const circumference = 2 * Math.PI * 45; // radius = 45
  let currentOffset = 0;

  const segments = data.map((segment) => {
    const percentage = total > 0 ? (segment.value / total) * 100 : 0;
    const dashLength = (percentage / 100) * circumference;
    const offset = currentOffset;
    currentOffset += dashLength;
    return {
      ...segment,
      percentage,
      dashLength,
      offset,
    };
  });

  return (
    <div className="bg-bg-secondary border border-border rounded-xl p-5">
      <h3 className="text-sm font-medium text-text-secondary mb-4">{title}</h3>
      <div className="flex items-center gap-6">
        {/* SVG Donut */}
        <div className="relative" style={{ width: size, height: size }}>
          <svg
            viewBox="0 0 100 100"
            className="transform -rotate-90"
            style={{ width: size, height: size }}
          >
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="10"
              className="text-bg-primary"
            />
            {/* Data segments */}
            {segments.map((segment, index) => (
              <circle
                key={index}
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={segment.color}
                strokeWidth="10"
                strokeDasharray={`${segment.dashLength} ${circumference}`}
                strokeDashoffset={-segment.offset}
                className="transition-all duration-500"
              />
            ))}
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-2xl font-bold text-text-primary">{total}</p>
              <p className="text-xs text-text-secondary">Total</p>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-2">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: segment.color }}
              />
              <span className="text-sm text-text-secondary">
                {segment.label}
              </span>
              <span className="text-sm font-medium text-text-primary">
                {segment.value} ({segment.percentage.toFixed(0)}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
