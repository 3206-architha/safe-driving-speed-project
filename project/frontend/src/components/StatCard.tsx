interface Props {
  label: string;
  value: string | number;
  unit?: string;
  icon?: string;
}

export default function StatCard({ label, value, unit, icon }: Props) {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-1">
        <span className="text-slate-400 text-xs uppercase tracking-wide">{label}</span>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className="text-2xl font-semibold">
        {value}
        {unit && <span className="text-sm text-slate-400 ml-1">{unit}</span>}
      </div>
    </div>
  );
}
