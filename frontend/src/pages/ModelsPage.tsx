import React, { useEffect, useState } from 'react';
import { Cpu, CheckCircle2, AlertTriangle, Layers, BarChart3, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

export const ModelsPage: React.FC = () => {
  const [registry, setRegistry] = useState<Record<string, any> | null>(null);
  const [imgMetrics, setImgMetrics] = useState<any | null>(null);
  const [textMetrics, setTextMetrics] = useState<any | null>(null);

  useEffect(() => {
    api.getModels().then(setRegistry).catch(() => {});
    api.getModelMetrics('image_detector').then(setImgMetrics).catch(() => {});
    api.getModelMetrics('text_detector').then(setTextMetrics).catch(() => {});
  }, []);

  return (
    <div className="page-wrap flex flex-col gap-9 py-10 sm:gap-12">
      {/* Header */}
      <div>
        <span className="eyebrow"><Cpu className="h-3.5 w-3.5" />How the checks work</span>
        <h1 className="page-heading mt-4">Models & evaluation</h1>
        <p className="page-subtitle">See which model artifacts are available, what they analyze, and where their limits are.</p>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Model 1: EfficientNet-B0 */}
        <div className="surface-card flex flex-col gap-5 p-5 sm:p-7">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-600" />
              <h2 className="font-bold text-slate-900 text-base">EfficientNet-B0 Image Classifier</h2>
            </div>
            <span className="text-[11px] font-semibold bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded border border-emerald-200">
              {registry?.image_detector?.status === 'active' ? 'Checkpoint loaded' : 'No trained checkpoint'}
            </span>
          </div>

          <div className="text-xs text-slate-600 space-y-2">
            <p>
              <strong>Architecture:</strong> Pretrained Convolutional Neural Network (EfficientNet-B0) with replaced binary classification head.
            </p>
            <p>
              <strong>Transfer Learning:</strong> Freezes lower feature extractor stages to retain edge & gradient primitives while fine-tuning top convolutional blocks on generative synthetic artifacts.
            </p>
            <p>
              <strong>Interpretability:</strong> Layer-CAM / Grad-CAM visualizer hooking into <code className="bg-slate-100 px-1 py-0.5 rounded">model.features[-1]</code> to isolate spatial pixel regions driving prediction.
            </p>
          </div>

          {imgMetrics?.status === 'evaluated' && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col gap-3">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-blue-600" />
                Held-Out Benchmark Metrics
              </span>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                <div className="bg-white border border-slate-200 p-2 rounded">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Accuracy</span>
                  <div className="text-sm font-bold text-slate-900 font-mono">{(imgMetrics.accuracy * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-white border border-slate-200 p-2 rounded">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Precision</span>
                  <div className="text-sm font-bold text-slate-900 font-mono">{(imgMetrics.precision * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-white border border-slate-200 p-2 rounded">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Recall</span>
                  <div className="text-sm font-bold text-slate-900 font-mono">{(imgMetrics.recall * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-white border border-slate-200 p-2 rounded">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">ROC-AUC</span>
                  <div className="text-sm font-bold text-slate-900 font-mono">{imgMetrics.roc_auc.toFixed(3)}</div>
                </div>
              </div>

              {imgMetrics.confusion_matrix && (
                <div className="text-[11px] font-mono text-slate-600 bg-white border border-slate-200 p-2 rounded">
                  Confusion Matrix: TN={imgMetrics.confusion_matrix.true_negative}, FP={imgMetrics.confusion_matrix.false_positive}, FN={imgMetrics.confusion_matrix.false_negative}, TP={imgMetrics.confusion_matrix.true_positive}
                </div>
              )}
            </div>
          )}
          {imgMetrics?.status === 'not_evaluated' && <p className="text-xs text-amber-700">{imgMetrics.evaluation_note}</p>}
        </div>

        {/* Model 2: TF-IDF + Logistic Regression */}
        <div className="surface-card flex flex-col gap-5 p-5 sm:p-7">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-600" />
              <h2 className="font-bold text-slate-900 text-base">TF-IDF Text Threat Classifier</h2>
            </div>
            <span className="text-[11px] font-semibold bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded border border-emerald-200">
              {registry?.text_detector?.status === 'demo' ? 'Demo model (40 examples)' : registry?.text_detector?.model_version || 'Unavailable'}
            </span>
          </div>

          <div className="text-xs text-slate-600 space-y-2">
            <p>
              <strong>Pipeline:</strong> Scikit-learn Pipeline with <code className="bg-slate-100 px-1 py-0.5 rounded">TfidfVectorizer(ngram=(1,2), sublinear_tf=True)</code> and Multinomial Logistic Regression.
            </p>
            <p>
              <strong>Taxonomy:</strong> Multi-class intent mapping across <span className="font-semibold text-slate-800">{registry?.text_detector?.classes?.join(", ") || "Not available"}</span>.
            </p>
            <p>
              <strong>Explainability:</strong> Direct feature contribution coefficients extracted via dot product of token TF-IDF weights and class hyperplanes.
            </p>
          </div>

          {textMetrics?.status === 'evaluated' && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col gap-3">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-blue-600" />
                Per-Class Performance
              </span>

              <div className="divide-y divide-slate-200 bg-white border border-slate-200 rounded">
                {Object.entries(textMetrics.per_class_metrics || {}).map(([cls, m]: [string, any]) => (
                  <div key={cls} className="p-2 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-800 capitalize">{cls.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-3 font-mono text-[11px] text-slate-600">
                      <span>P: {m.precision}</span>
                      <span>R: {m.recall}</span>
                      <span className="text-blue-600 font-semibold">F1: {m.f1}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="text-[11px] text-slate-500 text-right">
                Macro F1: <strong className="font-mono text-slate-800">{textMetrics.macro_f1}</strong> •
                Weighted F1: <strong className="font-mono text-slate-800">{textMetrics.weighted_f1}</strong>
              </div>
            </div>
          )}
          {textMetrics?.status === 'not_evaluated' && <p className="text-xs text-amber-700">{textMetrics.evaluation_note}</p>}
        </div>
      </div>

      {/* Centralized Risk Engine Policy Card */}
      <div className="surface-card flex flex-col gap-4 p-5 sm:p-7">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-600" />
          <h2 className="font-bold text-slate-900 text-base">Centralized Heuristic Risk Engine Policy</h2>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          AI-media scores are informational and do not raise scam risk by themselves. Page warnings rely on suspicious URL signals
          or concrete credential and payment requests; page-wide classifier guesses alone are not treated as proof:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div className="border border-emerald-200 bg-emerald-50/50 p-3 rounded-lg">
            <span className="font-bold text-emerald-800">Low Risk (0–29)</span>
            <p className="text-emerald-700 text-[11px] mt-1">No strong scam, phishing, or suspicious-link indicators in the available checks.</p>
          </div>
          <div className="border border-amber-200 bg-amber-50/50 p-3 rounded-lg">
            <span className="font-bold text-amber-800">Moderate Risk (30–59)</span>
            <p className="text-amber-700 text-[11px] mt-1">A limited security signal needs context and review.</p>
          </div>
          <div className="border border-orange-200 bg-orange-50/50 p-3 rounded-lg">
            <span className="font-bold text-orange-800">High Risk (60–84)</span>
            <p className="text-orange-700 text-[11px] mt-1">Stronger evidence of fraud, credential theft, impersonation, or a deceptive link.</p>
          </div>
          <div className="border border-rose-200 bg-rose-50/50 p-3 rounded-lg">
            <span className="font-bold text-rose-800">Critical Risk (85–100)</span>
            <p className="text-rose-700 text-[11px] mt-1">Several independent security indicators point to a serious threat.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
