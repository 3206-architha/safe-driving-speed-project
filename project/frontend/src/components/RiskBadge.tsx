interface Props {
  level: 'Low' | 'Medium' | 'High';
  size?: 'sm' | 'lg';
}

const STYLES: Record<string, string> = {
  Low: 'bg-green-500/15 text-green-400 border-green-500/30',
  Medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  High: 'bg-red-500/15 text-red-400 border-red-500/30',
};

export default function RiskBadge({ level, size = 'sm' }: Props) {
  const sizeClass = size === 'lg' ? 'text-base px-4 py-1.5' : 'text-xs px-2.5 py-1';
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${STYLES[level]} ${sizeClass}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {level} Risk
    </span>
  );
}
