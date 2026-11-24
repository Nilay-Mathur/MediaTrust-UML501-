import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  History, Search, Trash2, ArrowRight, ShieldCheck, 
  Filter, FileText, RefreshCw 
} from 'lucide-react';
import { api } from '../services/api';
import { AnalysisHistoryItem, AnalyticsSummary } from '../types';
import { RiskBadge } from '../components/RiskBadge';

export const HistoryPage: React.FC = () => {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedRisk, setSelectedRisk] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [dateWindow, setDateWindow] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');

  const loadData = () => {
    setLoading(true);
    Promise.all([
      api.getAnalyses(selectedType || undefined, selectedRisk || undefined),
      api.getAnalyticsSummary(),
    ])
      .then(([historyItems, summary]) => {
        setItems(historyItems);
        setAnalytics(summary);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [selectedRisk, selectedType]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm('Delete this analysis record permanently?')) {
      try {
        await api.deleteAnalysis(id);
        setItems((prev) => prev.filter((i) => i.analysis_id !== id));
        api.getAnalyticsSummary().then(setAnalytics).catch(() => {});
      } catch (err: any) {
        alert(err.message || 'Deletion failed.');
      }
    }
  };

  const filteredItems = items.filter((item) => {
    const q = searchQuery.trim().toLowerCase();
    const matchesSearch = !q || (
      item.analysis_id.toLowerCase().includes(q) ||
      (item.source_reference && item.source_reference.toLowerCase().includes(q)) ||
      item.summary.toLowerCase().includes(q)
    );
    const days = dateWindow === '24h' ? 1 : dateWindow === '7d' ? 7 : dateWindow === '30d' ? 30 : null;
    const cutoff = days ? Date.now() - days * 24 * 60 * 60 * 1000 : null;
    return matchesSearch && (!cutoff || new Date(item.created_at).getTime() >= cutoff);
  }).sort((a, b) => {
    const delta = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    return sortOrder === 'newest' ? -delta : delta;
  });

  return (
    <div className="page-wrap flex flex-col gap-8 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="eyebrow"><History className="h-3.5 w-3.5" />Saved locally</span>
          <h1 className="page-heading mt-4">Your analysis history</h1>
          <p className="page-subtitle">Find a past check, review its evidence, or remove its saved record.</p>
        </div>
        <button
          type="button"
          onClick={loadData}
          className="btn-secondary self-start px-4 py-2.5 text-xs sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
          Refresh
        </button>
      </div>

      {/* Aggregate Real Statistics */}
      {analytics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="surface-card p-4">
            <span className="text-xs text-slate-500 font-medium">Total Inferences</span>
            <div className="text-2xl font-bold text-slate-900 mt-1 font-mono">
              {analytics.total_analyses}
            </div>
          </div>
          <div className="surface-card border-emerald-200 p-4">
            <span className="text-xs text-emerald-700 font-medium">Low Risk Clean</span>
            <div className="text-2xl font-bold text-emerald-800 mt-1 font-mono">
              {analytics.risk_breakdown.low}
            </div>
          </div>
          <div className="surface-card border-amber-200 p-4">
            <span className="text-xs text-amber-700 font-medium">Moderate / Caution</span>
            <div className="text-2xl font-bold text-amber-800 mt-1 font-mono">
              {analytics.risk_breakdown.moderate}
            </div>
          </div>
          <div className="surface-card border-rose-200 p-4">
            <span className="text-xs text-rose-700 font-medium">High & Critical Threats</span>
            <div className="text-2xl font-bold text-rose-800 mt-1 font-mono">
              {analytics.risk_breakdown.high + analytics.risk_breakdown.critical}
            </div>
          </div>
        </div>
      )}

      {/* Filters and Search Bar */}
      <div className="surface-card flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ID, URL, or keyword..."
            className="w-full pl-9 pr-3 py-2.5 text-sm"
          />
        </div>

        <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-3 md:w-auto">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="min-w-0 px-3 py-2.5 text-sm"
          >
            <option value="">All Input Types</option>
            <option value="image">Images</option>
            <option value="video">Videos</option>
            <option value="text">Text & Scams</option>
            <option value="url">URLs</option>
            <option value="impersonation">Impersonation</option>
            <option value="page">Webpages</option>
          </select>

          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="min-w-0 px-3 py-2.5 text-sm"
          >
            <option value="">All Risk Tiers</option>
            <option value="low">Low Risk</option>
            <option value="moderate">Moderate Risk</option>
            <option value="high">High Risk</option>
            <option value="critical">Critical Risk</option>
          </select>
          <select aria-label="Filter by date" value={dateWindow} onChange={(e) => setDateWindow(e.target.value)} className="min-w-0 px-3 py-2.5 text-sm">
            <option value="all">Any date</option><option value="24h">Past 24 hours</option><option value="7d">Past 7 days</option><option value="30d">Past 30 days</option>
          </select>
        </div>
        <label className="sr-only" htmlFor="history-sort">Sort history</label>
        <select id="history-sort" aria-label="Sort history" value={sortOrder} onChange={(e) => setSortOrder(e.target.value as 'newest' | 'oldest')} className="w-full px-3 py-2.5 text-sm md:w-40">
          <option value="newest">Newest first</option><option value="oldest">Oldest first</option>
        </select>
      </div>

      {/* History List */}
      <div className="surface-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading audit history...</div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center gap-2">
            <FileText className="w-8 h-8 text-slate-300 stroke-1" />
            <p className="text-xs font-medium text-slate-600">No records match your filters.</p>
            <Link to="/workspace" className="text-xs text-blue-600 font-semibold hover:underline mt-1">
              Run an analysis in Workspace
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredItems.map((item) => (
              <Link
                key={item.analysis_id}
                to={`/analysis/${item.analysis_id}`}
                className="p-4 hover:bg-slate-50 transition flex items-center justify-between gap-4 block"
              >
                <div className="flex flex-col gap-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-semibold text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded">
                      {item.analysis_id}
                    </span>
                    <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                      {item.input_type}
                    </span>
                    <span className="text-slate-300">•</span>
                    <span className="text-xs text-slate-500">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>

                  <p className="text-xs font-medium text-slate-800 truncate max-w-xl">
                    {item.summary}
                  </p>

                  {item.source_reference && (
                    <span className="text-[11px] text-slate-400 truncate">
                      Source: {item.source_reference}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <RiskBadge risk={item.overall_risk} score={item.risk_score} size="sm" />
                  <button
                    type="button"
                    onClick={(e) => handleDelete(item.analysis_id, e)}
                    title="Delete record"
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
