import { AnalysisResponse, AnalysisHistoryItem, SystemStatus, AnalyticsSummary } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errDetail = 'An unexpected server error occurred.';
    try {
      const errJson = await res.json();
      errDetail = errJson.detail || errJson.message || errDetail;
    } catch {
      errDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse(res);
  },

  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch(`${API_BASE_URL}/system/status`);
    return handleResponse(res);
  },

  async analyzeImage(file: File, claimedHash?: string): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (claimedHash) {
      formData.append('claimed_hash', claimedHash);
    }
    const res = await fetch(`${API_BASE_URL}/analyze/image`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async analyzeVideo(file: File): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/analyze/video`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async analyzeText(text: string, claimedSender?: string, contextUrl?: string): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/analyze/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        claimed_sender: claimedSender || undefined,
        context_url: contextUrl || undefined,
      }),
    });
    return handleResponse(res);
  },

  async analyzeUrl(url: string, enableNetworkChecks: boolean = false): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/analyze/url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        enable_network_checks: enableNetworkChecks,
      }),
    });
    return handleResponse(res);
  },

  async analyzeImpersonation(
    claimedEntity: string,
    messageText?: string,
    profileHandle?: string,
    domain?: string
  ): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/analyze/impersonation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        claimed_entity: claimedEntity,
        message_text: messageText || undefined,
        profile_handle: profileHandle || undefined,
        domain: domain || undefined,
      }),
    });
    return handleResponse(res);
  },

  async getAnalyses(inputType?: string, risk?: string, limit: number = 50): Promise<AnalysisHistoryItem[]> {
    const params = new URLSearchParams();
    if (inputType) params.append('input_type', inputType);
    if (risk) params.append('risk', risk);
    params.append('limit', limit.toString());

    const res = await fetch(`${API_BASE_URL}/analyses?${params.toString()}`);
    return handleResponse(res);
  },

  async getAnalysisById(analysisId: string): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/analyses/${analysisId}`);
    return handleResponse(res);
  },

  async deleteAnalysis(analysisId: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE_URL}/analyses/${analysisId}`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const res = await fetch(`${API_BASE_URL}/analytics/summary`);
    return handleResponse(res);
  },

  async getModels(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE_URL}/models`);
    return handleResponse(res);
  },

  async getModelMetrics(modelName: string): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE_URL}/models/${modelName}/metrics`);
    return handleResponse(res);
  },
};
