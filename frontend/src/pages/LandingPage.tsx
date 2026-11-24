import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowDownRight, ArrowRight, Check, Chrome, FileSearch, Image, Link2, MessageSquareText, ShieldCheck, Sparkles, Video } from 'lucide-react';
import { api } from '../services/api';
import { SystemStatus } from '../types';

const checks = [
  { icon: Image, tint: 'bg-clay-100 text-clay-700', title: 'Images', copy: 'Review a still image for synthetic-media signals and, when available, see a Grad-CAM view.' },
  { icon: Video, tint: 'bg-violet-100 text-violet-700', title: 'Videos & reels', copy: 'Sample frames from a video and show the model signals separately from scam risk.' },
  { icon: MessageSquareText, tint: 'bg-amber-100 text-amber-800', title: 'Messages', copy: 'Check text for patterns associated with fraud, phishing, or impersonation.' },
  { icon: Link2, tint: 'bg-leaf-100 text-leaf-800', title: 'Links', copy: 'Inspect a URL for suspicious structure and related security indicators.' },
];

export const LandingPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [serviceState, setServiceState] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    let mounted = true;
    api.getSystemStatus().then((value) => { if (mounted) { setStatus(value); setServiceState('online'); } }).catch(() => { if (mounted) setServiceState('offline'); });
    return () => { mounted = false; };
  }, []);

  return (
    <div className="pb-12">
      <section className="relative overflow-hidden border-b border-stone-200 bg-[#f4eee4]">
        <div className="pointer-events-none absolute -right-20 -top-32 h-[28rem] w-[28rem] rounded-full border-[70px] border-white/30" />
        <div className="page-wrap relative grid gap-12 py-14 sm:py-20 lg:grid-cols-[1.08fr_.92fr] lg:items-center lg:py-24">
          <div>
            <div className="eyebrow"><Sparkles className="h-3.5 w-3.5" />A practical second look at online content</div>
            <h1 className="mt-6 max-w-3xl text-4xl font-bold leading-[1.08] tracking-[-.045em] text-ink-900 sm:text-5xl lg:text-[3.7rem]">Understand the signal.<br /><span className="text-clay-700">Keep your judgment.</span></h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-stone-600 sm:text-lg">MediaTrust helps you inspect media, messages, and links that feel off. It shows the checks it ran, the evidence it found, and where the result is uncertain.</p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/workspace" className="btn-primary">Open the workspace <ArrowRight className="h-4 w-4" /></Link>
              <Link to="/extension-guide" className="btn-secondary"><Chrome className="h-4 w-4" />Set up the extension</Link>
            </div>
            <div className={`mt-7 inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs ${serviceState === 'online' ? 'border-emerald-200 bg-white/80 text-emerald-800' : serviceState === 'offline' ? 'border-rose-200 bg-white/80 text-rose-800' : 'border-stone-200 bg-white/80 text-stone-600'}`}>
              <span className={`h-2 w-2 rounded-full ${serviceState === 'online' ? 'bg-emerald-500' : serviceState === 'offline' ? 'bg-rose-500' : 'animate-pulse bg-stone-400'}`} />
              {serviceState === 'online' ? `Local analysis service is ready${status?.version ? ` · v${status.version}` : ''}` : serviceState === 'offline' ? 'Analysis service is offline · start the backend to run checks' : 'Checking local analysis service…'}
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl">
            <div className="absolute -left-4 -top-5 h-20 w-20 rounded-[28px] bg-clay-200/70" />
            <div className="relative rounded-[2rem] border border-white/80 bg-white p-5 shadow-soft sm:p-7">
              <div className="flex items-center justify-between gap-3 border-b border-stone-100 pb-5">
                <div><p className="text-xs font-semibold uppercase tracking-[.15em] text-stone-500">A guided check</p><h2 className="mt-1 text-lg font-bold text-ink-900">From question to evidence</h2></div>
                <span className="grid h-11 w-11 place-items-center rounded-2xl bg-ink-900 text-lime-300"><ShieldCheck className="h-5 w-5" /></span>
              </div>
              <div className="space-y-1 py-4">
                {[
                  { n: '01', icon: FileSearch, title: 'Choose what to inspect', copy: 'Media, text, a link, or a claimed identity.' },
                  { n: '02', icon: Activity, title: 'Review the available checks', copy: 'See model signals and observed evidence separately.' },
                  { n: '03', icon: ArrowDownRight, title: 'Decide what to do next', copy: 'Use the report as context, then verify important claims.' },
                ].map((step, index) => <div key={step.n} className="flex gap-4 rounded-2xl px-3 py-4 transition hover:bg-paper">
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-clay-50 text-clay-700"><step.icon className="h-5 w-5" /></span>
                  <div className="min-w-0"><p className="text-[11px] font-semibold tracking-wider text-clay-700">STEP {step.n}</p><h3 className="mt-0.5 text-sm font-semibold text-ink-900">{step.title}</h3><p className="mt-1 text-xs leading-5 text-stone-500">{step.copy}</p></div>
                  {index < 2 && <span className="sr-only">Continue to next step</span>}
                </div>)}
              </div>
              <div className="rounded-2xl bg-[#f8f4eb] px-4 py-3 text-xs leading-5 text-stone-600"><strong className="text-ink-900">A note on scores:</strong> these are uncertain signals, not proof that something is AI-generated or a scam.</div>
            </div>
            <div className="absolute -bottom-4 -right-3 hidden items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-xs font-medium text-ink-900 shadow-card sm:flex"><Check className="h-4 w-4 text-leaf-600" />Evidence stays visible in the report</div>
          </div>
        </div>
      </section>

      <section className="page-wrap py-16 sm:py-20">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="eyebrow">What you can check</p><h2 className="mt-4 text-2xl font-bold tracking-tight text-ink-900 sm:text-3xl">One place for a closer look</h2></div><p className="max-w-md text-sm leading-6 text-stone-600">Choose the type of content you have. MediaTrust only reports checks supported by the current service.</p></div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {checks.map(({ icon: Icon, tint, title, copy }) => <Link key={title} to="/workspace" className="surface-card group p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-600">
            <span className={`grid h-11 w-11 place-items-center rounded-2xl ${tint}`}><Icon className="h-5 w-5" /></span>
            <h3 className="mt-5 flex items-center justify-between font-semibold text-ink-900">{title}<ArrowRight className="h-4 w-4 text-stone-400 transition group-hover:translate-x-1 group-hover:text-clay-700" /></h3>
            <p className="mt-2 text-sm leading-6 text-stone-600">{copy}</p>
          </Link>)}
        </div>
      </section>

      <section className="page-wrap pb-8">
        <div className="grid gap-6 rounded-[2rem] bg-ink-900 p-6 text-white sm:p-9 lg:grid-cols-[.85fr_1.15fr] lg:items-center">
          <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-lime-300">Start in three steps</p><h2 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">Get from setup to a useful report.</h2><p className="mt-3 max-w-md text-sm leading-6 text-stone-300">You can use the website for one-off checks or install the browser extension for supported pages.</p></div>
          <div className="grid gap-3 sm:grid-cols-3">
            {[['1', 'Start the backend', 'The local service powers analysis.'], ['2', 'Choose a check', 'Upload content or paste a link or message.'], ['3', 'Read the evidence', 'Open a report to see what informed the result.']].map(([number, title, copy]) => <div key={number} className="rounded-2xl border border-white/10 bg-white/[.06] p-4"><span className="text-xs font-bold text-lime-300">{number.padStart(2, '0')}</span><h3 className="mt-3 text-sm font-semibold">{title}</h3><p className="mt-1 text-xs leading-5 text-stone-300">{copy}</p></div>)}
          </div>
        </div>
      </section>
    </div>
  );
};
