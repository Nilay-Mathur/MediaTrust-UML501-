import React, { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Activity, AlertCircle, Check, ChevronDown, Cpu, History, Menu, ShieldCheck, X } from 'lucide-react';
import { api } from '../services/api';

const links = [
  { path: '/', label: 'Overview' },
  { path: '/workspace', label: 'Workspace', icon: Activity },
  { path: '/history', label: 'History', icon: History },
  { path: '/models', label: 'Models', icon: Cpu },
  { path: '/extension-guide', label: 'Extension' },
];

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    api.getHealth().then(() => mounted && setBackendOnline(true)).catch(() => mounted && setBackendOnline(false));
    return () => { mounted = false; };
  }, [location.pathname]);

  useEffect(() => setMenuOpen(false), [location.pathname]);

  return (
    <header className="sticky top-0 z-40 border-b border-stone-200/80 bg-paper/95 backdrop-blur-md">
      <div className="mx-auto flex h-[72px] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="group flex items-center gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500" aria-label="MediaTrust home">
          <span className="grid h-10 w-10 place-items-center rounded-2xl bg-ink-900 text-lime-300 shadow-soft transition group-hover:-rotate-3">
            <ShieldCheck className="h-5 w-5" />
          </span>
          <span>
            <span className="flex items-center gap-2 text-[15px] font-bold tracking-tight text-ink-900">MediaTrust<span className="rounded-md bg-clay-100 px-1.5 py-0.5 text-[10px] font-semibold text-clay-800">LOCAL</span></span>
            <span className="hidden text-[11px] text-stone-500 sm:block">A clearer view of online signals</span>
          </span>
        </Link>

        <nav aria-label="Main navigation" className="hidden items-center gap-1 lg:flex">
          {links.map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `inline-flex items-center gap-2 rounded-xl px-3 py-2 text-[13px] font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500 ${isActive ? 'bg-white text-ink-900 shadow-sm ring-1 ring-stone-200' : 'text-stone-600 hover:bg-white/70 hover:text-ink-900'}`}>
              {Icon && <Icon className="h-4 w-4 text-stone-500" />}{label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[11px] font-semibold ${backendOnline ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : backendOnline === false ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-stone-200 bg-white text-stone-500'}`} title={backendOnline ? 'Local analysis service is responding' : backendOnline === false ? 'Start the backend to run analyses' : 'Checking local analysis service'}>
            {backendOnline ? <Check className="h-3.5 w-3.5" /> : backendOnline === false ? <AlertCircle className="h-3.5 w-3.5" /> : <span className="h-2 w-2 animate-pulse rounded-full bg-stone-400" />}
            {backendOnline ? 'Service ready' : backendOnline === false ? 'Service offline' : 'Checking service'}
          </div>
          <Link to="/workspace" className="rounded-xl bg-clay-600 px-4 py-2.5 text-[12px] font-semibold text-white shadow-sm transition hover:bg-clay-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500 focus-visible:ring-offset-2">Start a check</Link>
        </div>

        <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-stone-200 bg-white text-ink-900 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500 lg:hidden" aria-label={menuOpen ? 'Close menu' : 'Open menu'} aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {menuOpen && <nav aria-label="Mobile navigation" className="border-t border-stone-200 bg-paper px-4 py-3 lg:hidden">
        <div className="mx-auto flex max-w-7xl flex-col gap-1">
          {links.map(({ path, label, icon: Icon }) => <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium ${isActive ? 'bg-white text-ink-900 shadow-sm' : 'text-stone-600 hover:bg-white'}`}>{Icon && <Icon className="h-4 w-4" />}{label}</NavLink>)}
          <div className="mt-2 flex items-center justify-between border-t border-stone-200 pt-3">
            <span className={`inline-flex items-center gap-2 text-xs font-medium ${backendOnline ? 'text-emerald-800' : 'text-stone-600'}`}>{backendOnline ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}{backendOnline ? 'Analysis service ready' : 'Analysis service offline'}</span>
            <Link to="/workspace" className="rounded-lg bg-clay-600 px-3 py-2 text-xs font-semibold text-white">Start a check</Link>
          </div>
        </div>
      </nav>}
    </header>
  );
};
