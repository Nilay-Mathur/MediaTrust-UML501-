import React from 'react';
import { Info } from 'lucide-react';

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'quiet' }> = ({ variant = 'primary', className = '', ...props }) => {
  const styles = {
    primary: 'bg-clay-600 text-white hover:bg-clay-700 shadow-sm',
    secondary: 'border border-stone-300 bg-white text-ink-900 hover:bg-stone-50',
    quiet: 'bg-transparent text-stone-600 hover:bg-stone-100 hover:text-ink-900',
  }[variant];
  return <button {...props} className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className}`} />;
};

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...props }) => <div {...props} className={`rounded-2xl border border-stone-200 bg-white shadow-card ${className}`} />;

export const Badge: React.FC<React.HTMLAttributes<HTMLSpanElement> & { tone?: 'neutral' | 'warm' | 'good' | 'caution' }> = ({ tone = 'neutral', className = '', ...props }) => {
  const tones = { neutral: 'border-stone-200 bg-stone-100 text-stone-700', warm: 'border-clay-200 bg-clay-50 text-clay-800', good: 'border-emerald-200 bg-emerald-50 text-emerald-800', caution: 'border-amber-200 bg-amber-50 text-amber-800' };
  return <span {...props} className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${tones[tone]} ${className}`} />;
};

export const Alert: React.FC<React.HTMLAttributes<HTMLDivElement> & { title?: string }> = ({ title, className = '', children, ...props }) => <div role="status" {...props} className={`flex gap-3 rounded-2xl border border-clay-200 bg-clay-50 p-4 text-sm text-clay-900 ${className}`}><Info className="mt-0.5 h-4 w-4 shrink-0" /><div>{title && <p className="font-semibold">{title}</p>}<div className={title ? 'mt-1 text-sm leading-5' : 'text-sm leading-5'}>{children}</div></div></div>;

export const EmptyState: React.FC<{ icon?: React.ReactNode; title: string; children?: React.ReactNode; action?: React.ReactNode; className?: string }> = ({ icon, title, children, action, className = '' }) => <div className={`flex flex-col items-center rounded-2xl border border-dashed border-stone-300 bg-white/60 px-6 py-12 text-center ${className}`}>{icon && <span className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-clay-50 text-clay-700">{icon}</span>}<h3 className="text-base font-semibold text-ink-900">{title}</h3>{children && <p className="mt-2 max-w-md text-sm leading-6 text-stone-600">{children}</p>}{action && <div className="mt-5">{action}</div>}</div>;

export const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => <div aria-hidden="true" className={`animate-pulse rounded-xl bg-stone-200/80 ${className}`} />;

export const Tooltip: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => <span className="group relative inline-flex">{children}<span role="tooltip" className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 w-max max-w-56 -translate-x-1/2 rounded-lg bg-ink-900 px-2.5 py-1.5 text-xs text-white opacity-0 shadow-soft transition group-hover:opacity-100 group-focus-within:opacity-100">{label}</span></span>;

type TabItem = { id: string; label: string; icon?: React.ComponentType<{ className?: string }> };
export const Tabs: React.FC<{ items: readonly TabItem[]; value: string; onChange: (value: string) => void; label: string }> = ({ items, value, onChange, label }) => <div role="tablist" aria-label={label} className="flex gap-1 overflow-x-auto rounded-2xl border border-stone-200 bg-stone-100/80 p-1.5">{items.map(({ id, label: title, icon: Icon }) => <button type="button" role="tab" aria-selected={value === id} key={id} onClick={() => onChange(id)} className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500 ${value === id ? 'bg-white text-ink-900 shadow-sm' : 'text-stone-600 hover:bg-white/70 hover:text-ink-900'}`}>{Icon && <Icon className="h-4 w-4" />}{title}</button>)}</div>;
