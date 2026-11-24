from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.analysis import AnalysisRecord
from app.schemas.analysis import AnalysisResponse

def save_analysis(db: Session, response: AnalysisResponse, source_reference: Optional[str] = None) -> AnalysisRecord:
    record = AnalysisRecord(
        id=response.analysis_id,
        input_type=response.input_type,
        status=response.status,
        overall_risk=response.overall_risk,
        risk_score=response.risk_score,
        score_type=response.score_type,
        classification_tag=response.classification_tag,
        classification_label=response.classification_label,
        confidence=response.confidence,
        summary=response.summary,
        content_hash=response.content_hash,
        source_reference=source_reference[:255] if source_reference else None,
    )
    record.findings = [f.model_dump() for f in response.findings]
    record.detector_results = response.detector_results
    record.limitations = response.limitations
    record.recommended_actions = response.recommended_actions
    record.model_versions = response.model_versions

    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_analyses(
    db: Session, 
    input_type: Optional[str] = None, 
    risk: Optional[str] = None, 
    limit: int = 50, 
    offset: int = 0
) -> List[AnalysisRecord]:
    q = db.query(AnalysisRecord)
    if input_type:
        q = q.filter(AnalysisRecord.input_type == input_type)
    if risk:
        q = q.filter(AnalysisRecord.overall_risk == risk)
    return q.order_by(AnalysisRecord.created_at.desc()).offset(offset).limit(limit).all()

def get_analysis_by_id(db: Session, analysis_id: str) -> Optional[AnalysisRecord]:
    return db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()

def delete_analysis(db: Session, analysis_id: str) -> bool:
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if record:
        db.delete(record)
        db.commit()
        return True
    return False

def get_analytics_summary(db: Session) -> Dict[str, Any]:
    total = db.query(AnalysisRecord).count()
    low = db.query(AnalysisRecord).filter(AnalysisRecord.overall_risk == "low").count()
    moderate = db.query(AnalysisRecord).filter(AnalysisRecord.overall_risk == "moderate").count()
    high = db.query(AnalysisRecord).filter(AnalysisRecord.overall_risk == "high").count()
    critical = db.query(AnalysisRecord).filter(AnalysisRecord.overall_risk == "critical").count()

    by_type = {}
    for t in ["image", "video", "text", "url", "impersonation", "page"]:
        by_type[t] = db.query(AnalysisRecord).filter(AnalysisRecord.input_type == t).count()

    return {
        "total_analyses": total,
        "risk_breakdown": {
            "low": low,
            "moderate": moderate,
            "high": high,
            "critical": critical
        },
        "by_input_type": by_type
    }
