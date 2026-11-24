import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check, ChevronDown, Chrome, CircleHelp, MousePointer2, Play, Server, ShieldAlert } from 'lucide-react';
import readme from '../../../README.md?raw';

const backendCommands = readme.match(/### 5\.1 Backend Setup[\s\S]*?```bash([\s\S]*?)```/)?.[1].trim();
const steps = [
  { title: 'Open Extensions', body: 'In Chrome, enter chrome://extensions in the address bar. In Edge, enter edge://extensions.', chip: 'Browser settings' },
  { title: 'Turn on Developer mode', body: 'Use the switch near the top-right of the Extensions page.', chip: 'One-time setup' },
  { title: 'Choose Load unpacked', body: 'The button appears after Developer mode is enabled.', chip: 'Add extension' },
  { title: 'Select the extension folder', body: 'Choose the project’s extension folder—the one containing manifest.json.', chip: 'Project folder' },
  { title: 'Pin and use MediaTrust', body: 'Pin the shield icon, open a supported page, then choose Inspect Current Page or Check Active Video / Reel.', chip: 'Ready to check' },
];

export const ExtensionGuidePage: React.FC = () => (
  <div className="page-wrap flex flex-col gap-9 py-10 sm:gap-12">
    <section className="grid gap-8 rounded-[2rem] bg-[#f4eee4] p-6 sm:p-9 lg:grid-cols-[1fr_auto] lg:items-center">
      <div><span className="eyebrow"><Chrome className="h-3.5 w-3.5" />Chrome & Microsoft Edge</span><h1 className="page-heading mt-4">A little setup.<br />A clearer second look.</h1><p className="page-subtitle">Load the extension from the project folder, keep the local backend running, and review supported pages as you browse.</p></div>
      <span className="grid h-24 w-24 place-items-center rounded-[2rem] bg-white text-clay-700 shadow-card"><ShieldAlert className="h-11 w-11" /></span>
    </section>

    <section>
      <div className="mb-6"><p className="eyebrow">Setup guide</p><h2 className="mt-3 text-2xl font-bold tracking-tight text-ink-900">Install the unpacked extension</h2><p className="mt-2 text-sm text-stone-600">Follow these steps once on the browser profile you use.</p></div>
      <ol className="relative grid gap-3 md:grid-cols-2">
        {steps.map((step, index) => <li key={step.title} className="surface-card relative flex gap-4 p-5 sm:p-6">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-clay-50 text-sm font-bold text-clay-700">{String(index + 1).padStart(2, '0')}</span>
          <div><span className="text-[11px] font-semibold uppercase tracking-[.12em] text-stone-400">{step.chip}</span><h3 className="mt-1 font-semibold text-ink-900">{step.title}</h3><p className="mt-1 text-sm leading-6 text-stone-600">{step.body}</p></div>
          {index === 4 && <Check className="absolute right-5 top-5 h-4 w-4 text-leaf-600" />}
        </li>)}
      </ol>
    </section>

    <section className="grid gap-4 lg:grid-cols-2">
      <div className="surface-card p-5 sm:p-6">
        <div className="flex items-start gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-leaf-50 text-leaf-800"><Server className="h-5 w-5" /></span><div><h2 className="font-semibold text-ink-900">The backend needs to be running</h2><p className="mt-1 text-sm leading-6 text-stone-600">The extension sends checks to your local MediaTrust service. If it shows disconnected, start the backend and reload the page you’re inspecting.</p></div></div>
        <a href="#backend-setup" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-clay-700 hover:text-clay-800">Open README backend setup <ArrowRight className="h-4 w-4" /></a>
      </div>
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 sm:p-6"><div className="flex items-start gap-3"><CircleHelp className="mt-0.5 h-5 w-5 shrink-0 text-amber-800" /><div><h2 className="font-semibold text-amber-950">What an alert means</h2><p className="mt-1 text-sm leading-6 text-amber-900">An alert is a model signal to review. AI-media scores and scam-risk checks are separate, and neither is proof by itself. Open the full report to inspect the evidence.</p><div className="mt-4 flex flex-wrap gap-2"><Link to="/workspace" className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-xs font-semibold text-ink-900 shadow-sm">Try the website <ArrowRight className="h-3.5 w-3.5" /></Link><span className="inline-flex items-center gap-2 rounded-xl border border-amber-200 px-3 py-2 text-xs font-medium text-amber-950"><MousePointer2 className="h-3.5 w-3.5" />Inspect or check the active reel</span></div></div></div></div>
    </section>

    <details id="backend-setup" className="surface-card group overflow-hidden">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5 font-semibold text-ink-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500 sm:p-6"><span className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-stone-100 text-stone-700"><Play className="h-4 w-4" /></span>README · Section 5.1 Backend Setup</span><ChevronDown className="h-4 w-4 transition group-open:rotate-180" /></summary>
      <div className="border-t border-stone-200 bg-stone-50 p-5 sm:p-6"><p className="mb-3 text-sm text-stone-600">These commands are taken from the project README.</p><pre className="overflow-x-auto rounded-2xl bg-ink-900 p-4 text-xs leading-6 text-stone-100"><code>{backendCommands || 'See README.md, section 5.1 Backend Setup.'}</code></pre></div>
    </details>
  </div>
);
