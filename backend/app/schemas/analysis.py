from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    evidence_id: str
    category: str
    description: str
    source_detector: str
    severity: str  # info, low, moderate, high, critical
    verification_status: str = "predicted"  # observed, predicted, externally_verified, unavailable
    supporting_data: Optional[Dict[str, Any]] = None
    version: Optional[str] = "1.0.0"

class AnalysisResponse(BaseModel):
    analysis_id: str
    input_type: str
    status: str = "completed"  # completed, failed, inconclusive
    overall_risk: str  # low, moderate, high, critical
    risk_score: int = Field(ge=0, le=100)
    score_type: str = "heuristic_risk_score"
    classification_tag: Optional[str] = "normal"  # 'ai_generated', 'scam', 'impersonation', 'normal'
    classification_label: Optional[str] = "No strong threat indicators in scanned content"
    confidence: Optional[float] = None
    summary: str
    content_hash: Optional[str] = None
    findings: List[EvidenceItem] = []
    detector_results: Dict[str, Any] = {}
    limitations: List[str] = []
    recommended_actions: List[str] = []
    model_versions: Dict[str, str] = {}
    timestamp: str

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000, description="Text snippet to inspect for fraud, phishing, scam, or impersonation.")
    claimed_sender: Optional[str] = Field(None, max_length=100, description="Optional claimed sender name or company (e.g., Chase Bank, Netflix).")
    context_url: Optional[str] = Field(None, max_length=500, description="Optional associated URL included in the message.")

class UrlAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=2048, description="Target URL to analyze.")
    enable_network_checks: bool = Field(False, description="Whether to perform SSRF-safe network probe (headers, redirects).")

class ImpersonationAnalysisRequest(BaseModel):
    claimed_entity: str = Field(..., min_length=2, max_length=120, description="Company, organization, or individual claimed.")
    message_text: Optional[str] = Field(None, max_length=10000, description="Message content claiming the identity.")
    profile_handle: Optional[str] = Field(None, max_length=100, description="Account username or handle.")
    domain: Optional[str] = Field(None, max_length=255, description="Domain or email address associated with the claim.")

class PageAnalysisRequest(BaseModel):
    url: str
    page_title: Optional[str] = None
    text_content: Optional[str] = Field(None, max_length=15000)
    image_urls: List[str] = []
    video_urls: List[str] = []
    links: List[str] = []
    frame_data_url: Optional[str] = Field(None, max_length=700000, description="Optional downscaled JPEG frame sampled by the extension.")
    video_frame_data_urls: List[str] = Field(default_factory=list, max_length=20, description="Up to 20 downscaled sequential JPEG frames for temporal video/deepfake analysis.")
    video_context: bool = Field(False, description="True when a supplied frame was sampled from a playing video or reel.")

class IntegrityVerifyRequest(BaseModel):
    claimed_hash: str = Field(..., min_length=64, max_length=64, description="Expected SHA-256 hash.")
    file_content_hash: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str
    version: str
    models_loaded: Dict[str, bool]
    model_details: Dict[str, Any]
    active_environment: str
    timestamp: str
