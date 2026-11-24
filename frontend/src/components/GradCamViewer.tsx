import React, { useState } from 'react';
import { Eye, Layers } from 'lucide-react';

interface GradCamViewerProps {
  originalImageSrc: string;
  gradCamOverlaySrc: string | null;
  aiScore: number;
}

export const GradCamViewer: React.FC<GradCamViewerProps> = ({
  originalImageSrc,
  gradCamOverlaySrc,
  aiScore,
}) => {
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);

  if (!gradCamOverlaySrc) {
    return (
      <div className="rounded-lg border border-slate-200 overflow-hidden bg-slate-900 text-white flex items-center justify-center p-4">
        <img src={originalImageSrc} alt="Analysis Preview" className="max-h-80 object-contain rounded" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="relative rounded-lg border border-slate-200 overflow-hidden bg-slate-950 flex items-center justify-center min-h-[260px] max-h-[420px]">
        <img
          src={showHeatmap ? gradCamOverlaySrc : originalImageSrc}
          alt="Visual Inspection"
          className="max-h-80 object-contain rounded transition-all duration-200"
        />

        <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur text-white text-xs px-2.5 py-1 rounded border border-slate-700">
          {showHeatmap ? 'Grad-CAM Feature Activation Map' : 'Original Input Frame'}
        </div>

        <div className="absolute top-3 right-3 bg-slate-900/80 backdrop-blur text-white text-xs px-2.5 py-1 rounded border border-slate-700 font-mono">
          AI Score: {(aiScore * 100).toFixed(1)}%
        </div>
      </div>

      <div className="flex items-center justify-between bg-slate-100 p-2.5 rounded-lg border border-slate-200 text-xs">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowHeatmap(false)}
            className={`px-3 py-1.5 rounded font-medium flex items-center gap-1.5 transition ${
              !showHeatmap
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            Original
          </button>
          <button
            type="button"
            onClick={() => setShowHeatmap(true)}
            className={`px-3 py-1.5 rounded font-medium flex items-center gap-1.5 transition ${
              showHeatmap
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            Grad-CAM Overlay
          </button>
        </div>
        <span className="text-slate-500 hidden sm:inline">
          Red zones indicate high model convolution activation
        </span>
      </div>
    </div>
  );
};
