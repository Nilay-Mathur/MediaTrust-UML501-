import React, { useState } from 'react';
import { EvidenceItem } from '../types';
import { AlertCircle, AlertTriangle, Info, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';

interface EvidenceTableProps {
  findings: EvidenceItem[];
}

export const EvidenceTable: React.FC<EvidenceTableProps> = ({ findings }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!findings || findings.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 bg-slate-50 border border-slate-200 rounded-lg text-sm">
        No anomalous risk findings detected for this analysis.
      </div>
    );
  }

  const getSeverityIcon = (sev: string) => {
    switch (sev) {
      case 'critical':
        return <ShieldAlert className="w-4 h-4 text-rose-600" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-orange-600" />;
      case 'moderate':
        return <AlertCircle className="w-4 h-4 text-amber-600" />;
      default:
        return <Info className="w-4 h-4 text-blue-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const map: Record<string, { label: string; class: string }> = {
      observed: { label: 'Observed Fact', class: 'bg-slate-100 text-slate-700 border-slate-200' },
      predicted: { label: 'Model Prediction', class: 'bg-purple-50 text-purple-700 border-purple-200' },
      externally_verified: { label: 'Externally Verified', class: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
      unavailable: { label: 'Unavailable Evidence', class: 'bg-amber-50 text-amber-700 border-amber-200' },
    };
    const s = map[status] || { label: status, class: 'bg-slate-50 text-slate-600 border-slate-200' };
    return (
      <span className={`text-[11px] px-2 py-0.5 rounded border font-medium ${s.class}`}>
        {s.label}
      </span>
    );
  };

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
      <div className="divide-y divide-slate-100">
        {findings.map((item) => {
          const isExpanded = expandedId === item.evidence_id;
          return (
            <div key={item.evidence_id} className="p-4 transition-colors hover:bg-paper/70">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{getSeverityIcon(item.severity)}</div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="font-semibold text-slate-900 text-sm">
                        {item.description}
                      </span>
                      {getStatusBadge(item.verification_status)}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>Source: <strong className="text-slate-700">{item.source_detector}</strong></span>
                      <span>•</span>
                      <span>Category: <strong className="text-slate-700">{item.category}</strong></span>
                    </div>
                  </div>
                </div>

                {item.supporting_data && Object.keys(item.supporting_data).length > 0 && (
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? null : item.evidence_id)}
                    aria-expanded={isExpanded}
                    aria-controls={`evidence-${item.evidence_id}`}
                    className="shrink-0 rounded-lg p-2 text-xs text-stone-600 hover:bg-stone-100 hover:text-ink-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay-500"
                  >
                    <span>{isExpanded ? 'Hide Evidence' : 'View Evidence'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>

              {isExpanded && item.supporting_data && (
                <div id={`evidence-${item.evidence_id}`} className="mt-3 border-t border-stone-100 pt-3 pl-7">
                  <pre className="text-xs font-mono bg-slate-900 text-slate-100 p-3 rounded overflow-x-auto">
                    {JSON.stringify(item.supporting_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
