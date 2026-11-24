export interface EvidenceItem {
  evidence_id: string;
  category: string;
  description: string;
  source_detector: string;
  severity: 'info' | 'low' | 'moderate' | 'high' | 'critical';
  verification_status: 'observed' | 'predicted' | 'externally_verified' | 'unavailable';
  supporting_data?: Record<string, any>;
  version?: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  input_type: 'image' | 'video' | 'text' | 'url' | 'impersonation' | 'page';
  status: 'completed' | 'failed' | 'inconclusive';
  overall_risk: 'low' | 'moderate' | 'high' | 'critical';
  risk_score: number;
  score_type: string;
  classification_tag?: string;
  classification_label?: string;
  confidence: number | null;
  summary: string;
  content_hash?: string;
  source_reference?: string;
  findings: EvidenceItem[];
  detector_results: Record<string, any>;
  limitations: string[];
  recommended_actions: string[];
  model_versions: Record<string, string>;
  timestamp: string;
  created_at?: string;
}

export interface AnalysisHistoryItem {
  analysis_id: string;
  input_type: string;
  status: string;
  overall_risk: 'low' | 'moderate' | 'high' | 'critical';
  risk_score: number;
  classification_tag?: string;
  classification_label?: string;
  summary: string;
  source_reference?: string;
  created_at: string;
}

export interface SystemStatus {
  status: string;
  version: string;
  models_loaded: Record<string, boolean>;
  model_details: Record<string, any>;
  active_environment: string;
  timestamp: string;
}

export interface AnalyticsSummary {
  total_analyses: number;
  risk_breakdown: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
  };
  by_input_type: Record<string, number>;
}
