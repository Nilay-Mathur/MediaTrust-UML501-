import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, BookOpen, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => (
  <footer className="mt-20 border-t border-stone-200 bg-white/70">
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
        <Link to="/" className="flex items-center gap-2 text-sm font-semibold text-ink-900"><ShieldCheck className="h-4 w-4 text-clay-600" />MediaTrust<span className="font-normal text-stone-500">· Digital trust tools</span></Link>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-stone-600">
          <Link to="/workspace" className="hover:text-clay-700">Workspace</Link>
          <Link to="/extension-guide" className="hover:text-clay-700">Extension guide</Link>
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-clay-700"><BookOpen className="h-3.5 w-3.5" />API docs</a>
        </div>
      </div>
      <div className="mt-6 flex items-start gap-2 border-t border-stone-200 pt-4 text-[11px] leading-relaxed text-stone-500">
        <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-clay-600" />
        <p>MediaTrust reports model signals and heuristic checks. They can be wrong: a score is not proof that content is AI-generated or a scam. Review the evidence and verify important claims independently.</p>
      </div>
    </div>
  </footer>
);
