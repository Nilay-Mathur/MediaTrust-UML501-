import React from 'react';

interface RiskBadgeProps {
  risk: 'low' | 'moderate' | 'high' | 'critical' | string;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ risk, score, size = 'md' }) => {
  const normalized = risk.toLowerCase();

  const styles = {
    low: 'bg-leaf-50 text-leaf-800 border-emerald-200',
    moderate: 'bg-amber-50 text-amber-900 border-amber-200',
    high: 'bg-clay-50 text-clay-800 border-clay-200',
    critical: 'bg-rose-50 text-rose-800 border-rose-200',
  }[normalized] || 'bg-slate-50 text-slate-700 border-slate-200';

  const dotColors = {
    low: 'bg-leaf-600',
    moderate: 'bg-amber-500',
    high: 'bg-clay-600',
    critical: 'bg-rose-500',
  }[normalized] || 'bg-slate-400';

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1 font-medium',
    lg: 'text-sm px-3.5 py-1.5 font-semibold',
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${styles} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColors}`} />
      <span className="capitalize">{risk} Risk</span>
      {score !== undefined && (
        <span className="font-mono opacity-80 pl-1 border-l border-current">
          {score}/100
        </span>
      )}
    </span>
  );
};
