import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine } from 'recharts';

interface FrameScore {
  frame_index: number;
  timestamp_sec: number;
  ai_generated_score: number;
  prediction: string;
}

interface FrameTimelineProps {
  frames: FrameScore[];
  aggregateScore: number;
  peakScore: number;
}

export const FrameTimeline: React.FC<FrameTimelineProps> = ({ frames, aggregateScore, peakScore }) => {
  if (!frames || frames.length === 0) {
    return null;
  }

  const data = frames.map((f) => ({
    time: `${f.timestamp_sec}s`,
    score: Math.round(f.ai_generated_score * 100),
    prediction: f.prediction,
  }));

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-col gap-3">
      <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
        <div>
          <span className="font-semibold text-slate-900">Sampled frame AI-media scores</span>
          <span className="text-slate-500 ml-2">({frames.length} frames evaluated)</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-600">
            Peak Anomaly: <strong className="text-rose-600 font-mono">{(peakScore * 100).toFixed(1)}%</strong>
          </span>
          <span className="text-slate-600">
            Conservative Aggregate: <strong className="text-blue-600 font-mono">{(aggregateScore * 100).toFixed(1)}%</strong>
          </span>
        </div>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="aiGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#64748b' }} stroke="#cbd5e1" />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} stroke="#cbd5e1" />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-slate-900 text-white text-xs p-2 rounded shadow border border-slate-700">
                      <div>Timestamp: <strong>{payload[0].payload.time}</strong></div>
                      <div>Synthetic Score: <strong>{payload[0].value}%</strong></div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={85} stroke="#c65d2e" strokeDasharray="3 3" label={{ value: '85% alert cutoff', fill: '#913d20', fontSize: 10 }} />
            <Area type="monotone" dataKey="score" stroke="#0284c7" strokeWidth={2} fillOpacity={1} fill="url(#aiGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <p className="text-[11px] text-slate-500">
        Scores show what the image model returned for sampled frames. A high score is an uncertain signal, not proof of AI generation.
      </p>
    </div>
  );
};
