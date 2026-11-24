import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Activity, Image as ImageIcon, Video as VideoIcon, MessageSquare, Globe, 
  UserCheck, Upload, ArrowRight, Loader2, AlertCircle, FileCheck 
} from 'lucide-react';
import { api } from '../services/api';
import { AnalysisResponse } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { GradCamViewer } from '../components/GradCamViewer';
import { Tabs } from '../components/ui';

export const WorkspacePage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'image' | 'video' | 'text' | 'url' | 'impersonation'>('image');

  // Form states
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [claimedHash, setClaimedHash] = useState<string>('');

  const [videoFile, setVideoFile] = useState<File | null>(null);

  const [textInput, setTextInput] = useState<string>('');
  const [claimedSender, setClaimedSender] = useState<string>('');
  const [contextUrl, setContextUrl] = useState<string>('');

  const [urlInput, setUrlInput] = useState<string>('');
  const [enableNetworkChecks, setEnableNetworkChecks] = useState<boolean>(false);

  const [claimedEntity, setClaimedEntity] = useState<string>('');
  const [impersonationDomain, setImpersonationDomain] = useState<string>('');
  const [impersonationText, setImpersonationText] = useState<string>('');

  // Execution states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    api.getHealth().then(() => mounted && setBackendOnline(true)).catch(() => mounted && setBackendOnline(false));
    return () => { mounted = false; };
  }, []);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        setErrorMessage('Choose a JPEG, PNG, or WebP image.');
        e.target.value = '';
        return;
      }
      if (file.size > 15 * 1024 * 1024) {
        setErrorMessage('This image is larger than 15 MB. Choose a smaller file.');
        e.target.value = '';
        return;
      }
      setErrorMessage(null);
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!['video/mp4', 'video/webm'].includes(file.type)) {
        setErrorMessage('Choose an MP4 or WebM video.');
        e.target.value = '';
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        setErrorMessage('This video is larger than 50 MB. Choose a smaller file.');
        e.target.value = '';
        return;
      }
      setErrorMessage(null);
      setVideoFile(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setResult(null);

    try {
      let res: AnalysisResponse;
      if (activeTab === 'image') {
        if (!imageFile) throw new Error('Please select an image file to analyze.');
        res = await api.analyzeImage(imageFile, claimedHash.trim() || undefined);
      } else if (activeTab === 'video') {
        if (!videoFile) throw new Error('Please select a video file to analyze.');
        res = await api.analyzeVideo(videoFile);
      } else if (activeTab === 'text') {
        if (!textInput.trim()) throw new Error('Please enter text content to analyze.');
        res = await api.analyzeText(textInput, claimedSender.trim() || undefined, contextUrl.trim() || undefined);
      } else if (activeTab === 'url') {
        if (!urlInput.trim()) throw new Error('Please enter a target URL.');
        res = await api.analyzeUrl(urlInput.trim(), enableNetworkChecks);
      } else {
        if (!claimedEntity.trim()) throw new Error('Please specify the claimed entity or organization.');
        res = await api.analyzeImpersonation(
          claimedEntity.trim(),
          impersonationText.trim() || undefined,
          undefined,
          impersonationDomain.trim() || undefined
        );
      }
      setResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Analysis request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'image', label: 'Image Analysis', icon: ImageIcon },
    { id: 'video', label: 'Video Analysis', icon: VideoIcon },
    { id: 'text', label: 'Text & Scam', icon: MessageSquare },
    { id: 'url', label: 'URL & Phishing', icon: Globe },
    { id: 'impersonation', label: 'Impersonation', icon: UserCheck },
  ] as const;

  return (
    <div className="page-wrap flex flex-col gap-8 py-10 sm:gap-10">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><span className="eyebrow"><Activity className="h-3.5 w-3.5" />Private local analysis</span>
          <h1 className="page-heading mt-4">What would you like to check?</h1>
          <p className="page-subtitle">Pick the closest match below. We’ll show which checks ran and what evidence informed the result.</p>
        </div>
        <div className={`inline-flex w-fit items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold ${backendOnline ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : backendOnline === false ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-stone-200 bg-white text-stone-600'}`}>
          <span className={`h-2 w-2 rounded-full ${backendOnline ? 'bg-emerald-500' : backendOnline === false ? 'bg-rose-500' : 'animate-pulse bg-stone-400'}`} />
          {backendOnline ? 'Analysis service ready' : backendOnline === false ? 'Backend is offline' : 'Checking service'}
        </div>
      </div>

      {/* Tabs */}
      <Tabs items={tabs} value={activeTab} label="Choose analysis type" onChange={(id) => {
        setActiveTab(id as typeof activeTab);
        setResult(null);
        setErrorMessage(null);
      }} />

      {/* Workspace Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="surface-card lg:col-span-7 p-5 sm:p-7">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="mb-1 border-b border-stone-100 pb-4">
              <p className="text-xs font-semibold uppercase tracking-[.14em] text-clay-700">{tabs.find((tab) => tab.id === activeTab)?.label}</p>
              <p className="mt-1 text-sm text-stone-600">{activeTab === 'image' ? 'Choose one image from your device.' : activeTab === 'video' ? 'Add a short video file to sample frames.' : activeTab === 'text' ? 'Paste the message or post text you want to review.' : activeTab === 'url' ? 'Enter the full web address you want to inspect.' : 'Tell us who the message claims to represent.'}</p>
            </div>
            {/* Image Mode */}
            {activeTab === 'image' && (
              <div className="flex flex-col gap-4">
                <label className="text-xs font-semibold text-slate-700">Upload Target Image</label>
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-blue-500 transition cursor-pointer relative bg-slate-50">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    aria-label="Choose an image to analyze"
                    onChange={handleImageChange}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <Upload className="w-8 h-8 text-slate-400 mb-2" />
                  <p className="text-xs font-medium text-slate-700">
                    {imageFile ? imageFile.name : 'Click to upload or drag image here'}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1">Supports JPEG, PNG, WebP (Max 15MB)</p>
                </div>

                {imagePreview && (
                  <div className="rounded border border-slate-200 p-2 bg-slate-50 flex items-center gap-3">
                    <img src={imagePreview} alt="Thumbnail" className="w-12 h-12 object-cover rounded" />
                    <div className="text-xs">
                      <span className="font-semibold text-slate-800">{imageFile?.name}</span>
                      <p className="text-slate-500 text-[11px]">
                        {(imageFile!.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                )}

                <div>
                  <label className="text-xs font-medium text-slate-700 block mb-1">
                    Optional Reference SHA-256 Hash
                  </label>
                  <input
                    type="text"
                    value={claimedHash}
                    onChange={(e) => setClaimedHash(e.target.value)}
                    placeholder="Compare against trusted 64-character hex hash"
                    className="w-full text-xs font-mono border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}

            {/* Video Mode */}
            {activeTab === 'video' && (
              <div className="flex flex-col gap-4">
                <label className="text-xs font-semibold text-slate-700">Upload Video File</label>
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-blue-500 transition cursor-pointer relative bg-slate-50">
                  <input
                    type="file"
                    accept="video/mp4,video/webm"
                    aria-label="Choose a video to analyze"
                    onChange={handleVideoChange}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <VideoIcon className="w-8 h-8 text-slate-400 mb-2" />
                  <p className="text-xs font-medium text-slate-700">
                    {videoFile ? videoFile.name : 'Click or drag video file here'}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Supports MP4 & WebM (Max 50MB, max 180s duration)
                  </p>
                </div>

                {videoFile && (
                  <div className="text-xs text-slate-600 bg-blue-50 border border-blue-200 p-3 rounded-lg flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-blue-600 shrink-0" />
                    <span>Selected: <strong>{videoFile.name}</strong> ({(videoFile.size / (1024*1024)).toFixed(1)} MB)</span>
                  </div>
                )}
              </div>
            )}

            {/* Text Mode */}
            {activeTab === 'text' && (
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Message or Post Content
                  </label>
                  <textarea
                    rows={5}
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Paste suspicious SMS, email, DM, or post text here..."
                    className="w-full text-xs border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-700 block mb-1">
                      Claimed Sender (Optional)
                    </label>
                    <input
                      type="text"
                      value={claimedSender}
                      onChange={(e) => setClaimedSender(e.target.value)}
                      placeholder="e.g. Chase Bank, Netflix, Apple"
                      className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-700 block mb-1">
                      Embedded URL (Optional)
                    </label>
                    <input
                      type="text"
                      value={contextUrl}
                      onChange={(e) => setContextUrl(e.target.value)}
                      placeholder="e.g. http://verify-secure.xyz"
                      className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* URL Mode */}
            {activeTab === 'url' && (
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Target URL to Inspect
                  </label>
                  <input
                    type="text"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://example-phishing-login.xyz/account"
                    className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2.5 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="networkCheck"
                    checked={enableNetworkChecks}
                    onChange={(e) => setEnableNetworkChecks(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <label htmlFor="networkCheck" className="text-xs text-slate-700">
                    Enable safe network probe (SSRF-hardened; prevents local/private network access)
                  </label>
                </div>
              </div>
            )}

            {/* Impersonation Mode */}
            {activeTab === 'impersonation' && (
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Claimed Organization or Individual
                  </label>
                  <input
                    type="text"
                    value={claimedEntity}
                    onChange={(e) => setClaimedEntity(e.target.value)}
                    placeholder="e.g. State Bank of India, Microsoft Support, Elon Musk"
                    className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-700 block mb-1">
                    Associated Origin Domain / Email
                  </label>
                  <input
                    type="text"
                    value={impersonationDomain}
                    onChange={(e) => setImpersonationDomain(e.target.value)}
                    placeholder="e.g. support@sbi-updates.xyz"
                    className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-700 block mb-1">
                    Message or Solicitation Text
                  </label>
                  <textarea
                    rows={4}
                    value={impersonationText}
                    onChange={(e) => setImpersonationText(e.target.value)}
                    placeholder="Details of the communication received..."
                    className="w-full text-xs border border-slate-300 rounded-lg p-3"
                  />
                </div>
              </div>
            )}

            {errorMessage && (
              <div role="alert" className="bg-rose-50 border border-rose-200 text-rose-800 text-sm p-4 rounded-xl flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3.5 disabled:cursor-wait"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Checking the selected content…
                </>
              ) : (
                <>
                  Analyze Content
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Real-time Inline Result Card */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div aria-live="polite" className="surface-card min-h-[380px] p-5 sm:p-7 flex flex-col justify-between">
            {result ? (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
                    Scam & security risk
                  </span>
                  <RiskBadge risk={result.overall_risk} score={result.risk_score} size="md" />
                </div>

                <div>
                  <h3 className="font-bold text-ink-900 text-base">{result.summary}</h3>
                  <p className="mt-2 text-xs leading-5 text-stone-500">AI-media scores, when present, are reported separately. Neither score is proof on its own.</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Analysis ID: <strong className="font-mono text-slate-700">{result.analysis_id}</strong>
                  </p>
                </div>

                {/* Visual Preview if image Grad-CAM available */}
                {result.detector_results?.image_detector?.grad_cam_overlay && imagePreview && (
                  <div className="mt-2">
                    <GradCamViewer
                      originalImageSrc={imagePreview}
                      gradCamOverlaySrc={result.detector_results.image_detector.grad_cam_overlay}
                      aiScore={result.detector_results.image_detector.ai_generated_score}
                    />
                  </div>
                )}

                {/* Findings Preview */}
                <div className="mt-2 flex flex-col gap-2">
                  <span className="text-xs font-semibold text-slate-700">
                    Key Findings ({result.findings.length})
                  </span>
                  <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    {result.findings.map((f) => (
                      <div key={f.evidence_id} className="text-xs bg-slate-50 border border-slate-100 p-2 rounded text-slate-700 flex items-start gap-1.5">
                        <span className="text-blue-600 font-bold">•</span>
                        <span>{f.description}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => navigate(`/analysis/${result.analysis_id}`)}
                  className="w-full mt-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold py-2.5 rounded-lg transition flex items-center justify-center gap-1.5 shadow-sm"
                >
                  View Full Audit Report & Export
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex h-full flex-col items-center justify-center p-6 text-center">
                <span className="grid h-14 w-14 place-items-center rounded-2xl bg-clay-50 text-clay-700"><FileCheck className="h-7 w-7 stroke-[1.5]" /></span>
                <p className="mt-4 text-sm font-semibold text-ink-900">Your report will appear here</p>
                <p className="mt-1 max-w-xs text-xs leading-5 text-stone-500">Choose a check, add the content, then select “Analyze”. You can open the full report to review every finding.</p>
                {backendOnline === false && <p className="mt-4 rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-900">The local backend is offline. Start it using the project README, section 5.1.</p>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
