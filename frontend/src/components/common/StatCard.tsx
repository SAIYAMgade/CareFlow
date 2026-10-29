import React from 'react';
import { LucideIcon, ArrowUpRight } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  subtext?: string;
  colorScheme?: 'default' | 'amber' | 'emerald' | 'blue' | 'rose' | 'purple';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon: Icon,
  subtext,
  colorScheme = 'default',
  onClick
}) => {
  const colorMap = {
    default: 'text-slate-600 bg-slate-100',
    blue: 'text-blue-600 bg-blue-50',
    amber: 'text-amber-600 bg-amber-50',
    emerald: 'text-emerald-600 bg-emerald-50',
    rose: 'text-rose-600 bg-rose-50',
    purple: 'text-purple-600 bg-purple-50'
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:border-slate-300 hover:shadow-md active:scale-[0.99]' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</span>
        <div className={`p-2.5 rounded-lg ${colorMap[colorScheme]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-4 flex items-baseline justify-between">
        <div className="text-3xl font-bold tracking-tight text-slate-900">{value}</div>
        {onClick && (
          <span className="flex items-center text-xs font-medium text-slate-400 group-hover:text-slate-600">
            View <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
          </span>
        )}
      </div>
      {subtext && <p className="mt-1 text-xs text-slate-500">{subtext}</p>}
    </div>
  );
};
