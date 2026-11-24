import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, Download, Trash2, Printer, Shield, 
  CheckCircle2, AlertTriangle, AlertCircle, FileText, Lock, Clock
} from 'lucide-react';
import { api } from '../services/api';
import { AnalysisResponse } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { EvidenceTable } from '../components/EvidenceTable';
import { GradCamViewer } from '../components/GradCamViewer';
import { FrameTimeline } from '../components/FrameTimeline';

export const AnalysisDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.getAnalysisById(id)
      .then(setData)
      .catch((err) => setError(err.message || 'Failed to load analysis record.'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    if (!data) return;
    if (window.confirm('Delete this analysis audit record permanently?')) {
      try {
        await api.deleteAnalysis(data.analysis_id);
        navigate('/history');
      } catch (err: any) {
        alert(err.message || 'Failed to delete record.');
      }
    }
  };

  const handleDownloadJson = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mediatrust-report-${data.analysis_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="page-wrap py-20">
        <div className="surface-card mx-auto max-w-xl p-8"><div className="h-2 w-32 animate-pulse rounded-full bg-clay-200" /><div className="mt-5 h-5 w-3/4 animate-pulse rounded bg-stone-200" /><p className="mt-3 text-sm text-stone-500">Loading the saved report…</p></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-wrap flex flex-col items-center gap-4 py-20 text-center">
        <AlertCircle className="w-10 h-10 text-rose-500" />
        <h2 className="text-xl font-bold text-slate-900">Record Not Found</h2>
        <p className="text-xs text-slate-500">{error || 'This analysis record does not exist or has been deleted.'}</p>
        <Link to="/workspace" className="text-xs font-semibold text-blue-600 hover:underline">
          Return to Workspace
        </Link>
      </div>
    );
  }

  const imageRes = data.detector_results?.image_detector;
  const videoRes = data.detector_results?.video_detector;
  const deepfakeRes = data.detector_results?.deepfake_video_detector;
  const textRes = data.detector_results?.text_detector;
  const provRes = data.detector_results?.provenance;

  return (
    <div className="page-wrap flex flex-col gap-7 py-8 sm:gap-9 print:p-0">
      {/* Back and Action Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-4 print:hidden">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => window.print()}
            className="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          >
            <Printer className="w-3.5 h-3.5 text-slate-500" />
            Print Report
          </button>
          <button
            type="button"
            onClick={handleDownloadJson}
            className="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Export JSON
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="bg-rose-50 border border-rose-200 hover:bg-rose-100 text-rose-700 text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-600" />
            Delete Record
          </button>
        </div>
      </div>

      {/* Main Report Card */}
      <div className="surface-card flex flex-col gap-6 rounded-[1.75rem] p-5 sm:p-8">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                {data.analysis_id}
              </span>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">
                {data.input_type} Inspection
              </span>
              {data.classification_label && (
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-900 text-white tracking-wide">
                  {data.classification_label}
                </span>
              )}
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              {data.summary}
            </h1>
            <div className="flex items-center gap-4 text-xs text-slate-500 mt-2 flex-wrap">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                {new Date(data.timestamp || data.created_at || '').toLocaleString()}
              </span>
              {data.source_reference && (
                <span>Source: <strong className="text-slate-700">{data.source_reference}</strong></span>
              )}
            </div>
          </div>

          <div className="sm:text-right shrink-0">
            <RiskBadge risk={data.overall_risk} score={data.risk_score} size="lg" />
            <p className="text-[11px] text-slate-400 mt-1">
              Scam & security indicators only
            </p>
          </div>
        </div>

        {(imageRes || videoRes || deepfakeRes) && (
          <section className="rounded-2xl border border-sky-200 bg-sky-50/70 p-4 sm:p-5 flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">AI-media screening scores</h2>
              <p className="text-xs text-slate-600 mt-1">These model scores are separate from the scam and security risk above. They are uncertain signals, not proof of AI generation or manipulation.</p>
            </div>
            {videoRes?.status === 'inconclusive' && (
              <div className="rounded-md border border-amber-100 bg-white p-3 text-xs text-amber-800">Video analysis inconclusive: {videoRes.error || 'not enough frames were sampled; no AI verdict was made.'}</div>
            )}
            <div className="grid gap-3 sm:grid-cols-2">
              {imageRes?.status === 'completed' && (
                <div className="rounded-2xl border border-sky-100 bg-white p-4">
                  <div className="text-xs font-semibold text-slate-700">Sampled still-image AI score</div>
                  <div className="mt-1 text-2xl font-bold tracking-tight text-sky-800">{(Number(imageRes.ai_generated_score || 0) * 100).toFixed(1)}%</div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-sky-100"><div className="h-full rounded-full bg-sky-600 transition-all" style={{ width: `${Math.max(0, Math.min(100, Number(imageRes.ai_generated_score || 0) * 100))}%` }} /></div>
                </div>
              )}
              {videoRes?.status === 'completed' && (
                <div className="rounded-2xl border border-sky-100 bg-white p-4">
                  <div className="text-xs font-semibold text-slate-700">Pooled video-frame AI score</div>
                  <div className="mt-1 text-2xl font-bold tracking-tight text-sky-800">{(Number(videoRes.aggregate_ai_score || 0) * 100).toFixed(1)}%</div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-sky-100"><div className="h-full rounded-full bg-sky-600 transition-all" style={{ width: `${Math.max(0, Math.min(100, Number(videoRes.aggregate_ai_score || 0) * 100))}%` }} /></div>
                  <div className="text-[11px] text-slate-500">Peak frame: {(Number(videoRes.peak_frame_score || 0) * 100).toFixed(1)}% · {videoRes.frames_analyzed || 0} frames</div>
                </div>
              )}
              {deepfakeRes?.status === 'completed' && (
                <div className="rounded-2xl border border-sky-100 bg-white p-4">
                  <div className="text-xs font-semibold text-slate-700">Face-deepfake model score</div>
                  <div className="mt-1 text-2xl font-bold tracking-tight text-sky-800">{(Number(deepfakeRes.fake_probability || 0) * 100).toFixed(1)}%</div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-sky-100"><div className="h-full rounded-full bg-sky-600 transition-all" style={{ width: `${Math.max(0, Math.min(100, Number(deepfakeRes.fake_probability || 0) * 100))}%` }} /></div>
                  <div className="text-[11px] text-slate-500">Face manipulation screening across {deepfakeRes.frames_analyzed || 0} frames</div>
                </div>
              )}
              {deepfakeRes?.status === 'inconclusive' && (
                <div className="rounded-md border border-amber-100 bg-white p-3 text-xs text-amber-800">Face-deepfake analysis inconclusive: {deepfakeRes.error}</div>
              )}
            </div>
          </section>
        )}

        {/* Visual Media Inspection (Grad-CAM or Timeline) */}
        {imageRes?.grad_cam_overlay && (
          <div className="flex flex-col gap-2">
            <h2 className="text-sm font-bold text-slate-900">Grad-CAM Activation Interpretability</h2>
            <GradCamViewer
              originalImageSrc={imageRes.grad_cam_overlay}
              gradCamOverlaySrc={imageRes.grad_cam_overlay}
              aiScore={imageRes.ai_generated_score}
            />
          </div>
        )}

        {videoRes?.frame_timeline && (
          <div className="flex flex-col gap-2">
            <h2 className="text-sm font-bold text-slate-900">Keyframe Anomaly Timeline</h2>
            <FrameTimeline
              frames={videoRes.frame_timeline}
              aggregateScore={videoRes.aggregate_ai_score}
              peakScore={videoRes.peak_frame_score}
            />
          </div>
        )}

        {/* Text Feature Explanations */}
        {textRes?.top_contributing_features && textRes.top_contributing_features.length > 0 && (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <h3 className="text-xs font-bold text-slate-900 mb-2">
              Top Token Contributors (Class: <span className="text-blue-600">{textRes.predicted_category}</span>)
            </h3>
            <div className="flex flex-wrap gap-2">
              {textRes.top_contributing_features.map((feat: any, idx: number) => (
                <div key={idx} className="bg-white border border-slate-200 px-2.5 py-1 rounded text-xs flex items-center gap-1.5 shadow-sm">
                  <span className="font-medium text-slate-800">{feat.feature}</span>
                  <span className="text-[11px] font-mono text-blue-600 bg-blue-50 px-1 rounded">
                    +{feat.importance}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Evidence Findings */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900">Itemized Evidence Findings</h2>
            <span className="text-xs text-slate-500 font-mono">
              {data.findings.length} findings logged
            </span>
          </div>
          <EvidenceTable findings={data.findings} />
        </div>

        {/* Cryptographic SHA-256 and Provenance */}
        {data.content_hash && (
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex flex-col gap-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
              <Lock className="w-3.5 h-3.5 text-blue-600" />
              <span>Cryptographic Content Integrity (SHA-256)</span>
            </div>
            <code className="text-xs font-mono bg-white p-2 rounded border border-slate-200 text-slate-800 break-all select-all">
              {data.content_hash}
            </code>
            {provRes?.has_exif_metadata !== undefined && (
              <p className="text-[11px] text-slate-500">
                EXIF Status: <strong>{provRes.has_exif_metadata ? 'Metadata present' : 'Stripped or absent'}</strong> •
                Camera signature: <strong>{provRes.has_camera_hardware_tags ? 'Preserved' : 'None detected'}</strong>
              </p>
            )}
          </div>
        )}

        {/* Recommended Actions */}
        {data.recommended_actions && data.recommended_actions.length > 0 && (
          <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4 flex flex-col gap-2">
            <h3 className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-blue-600" />
              Recommended Security Actions
            </h3>
            <ul className="list-disc list-inside text-xs text-slate-700 space-y-1 pl-1">
              {data.recommended_actions.map((act, idx) => (
                <li key={idx}>{act}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Model Limitations & Responsible Use */}
        {data.limitations && data.limitations.length > 0 && (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col gap-2 text-xs">
            <h3 className="font-semibold text-slate-700 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              Model Limitations & Evaluated Context
            </h3>
            <ul className="list-disc list-inside text-slate-500 space-y-1 pl-1">
              {data.limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Audit Footprint */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 flex-wrap gap-2">
          <span>MediaTrust Centralized Risk Policy Engine v1.0</span>
          <span>Verified Local Inference Audit</span>
        </div>
      </div>
    </div>
  );
};
