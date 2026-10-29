import React from 'react';

interface BadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ status, size = 'sm' }) => {
  const normalized = status.toUpperCase();
  let colorStyle = 'bg-slate-100 text-slate-700 border-slate-200';

  if (['COMPLETED', 'ACTIVE', 'NORMAL', 'RESOLVED', 'FINAL', 'UP'].includes(normalized)) {
    colorStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['CHECKED_IN', 'IN_PROGRESS', 'PENDING_REVIEW', 'AWAITING_RESULTS', 'URGENT'].includes(normalized)) {
    colorStyle = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (['SCHEDULED', 'OPEN', 'ROUTINE', 'MEDIUM'].includes(normalized)) {
    colorStyle = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (['CANCELLED', 'NO_SHOW', 'CRITICAL', 'HIGH', 'DOWN', 'DEGRADED'].includes(normalized)) {
    colorStyle = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (['STAT'].includes(normalized)) {
    colorStyle = 'bg-purple-50 text-purple-700 border-purple-200 animate-pulse';
  }

  const sizeStyle = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${colorStyle} ${sizeStyle}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};
