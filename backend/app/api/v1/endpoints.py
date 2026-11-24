import base64
import io
import json
import datetime
import re
from urllib.parse import urlsplit
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.logging import logger
from app.database.session import get_db
from app.schemas.analysis import (
    AnalysisResponse, TextAnalysisRequest, UrlAnalysisRequest,
    ImpersonationAnalysisRequest, PageAnalysisRequest, IntegrityVerifyRequest,
    SystemStatusResponse
)
from app.security.file_validator import validate_image_file, validate_video_file, sanitize_filename
from app.ml.image_detector.service import image_detector_service
from app.ml.video_detector.service import video_detector_service
from app.ml.deepfake_video_detector.service import deepfake_video_detector_service
from app.ml.text_detector.service import text_detector_service
from app.ml.url_analyzer.service import url_analyzer_service
from app.ml.provenance.service import provenance_service
from app.ml.risk_engine.engine import risk_engine
from app.services import history_service

router = APIRouter()

@router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@router.get("/system/status", response_model=SystemStatusResponse, tags=["System"])
def system_status():
    return SystemStatusResponse(
        status="operational",
        version=settings.VERSION,
        models_loaded={
            "image_detector": image_detector_service.model_loaded,
            "text_detector": text_detector_service.model_loaded,
            "video_detector": image_detector_service.model_loaded,
            "face_deepfake_video_detector": deepfake_video_detector_service.model_loaded,
            "url_analyzer": True,
            "provenance_verifier": True,
            "centralized_risk_engine": True
        },
        model_details={
            "image_detector": {
                "backbone": "EfficientNet-B0",
                "task": "Binary Real vs AI-Generated Image Classification",
                "explainability": "Grad-CAM Activation Mapping"
            },
            "text_detector": {
                "architecture": "TF-IDF (1-2 ngrams) + Logistic Regression",
                "classes": list(text_detector_service.pipeline.named_steps["classifier"].classes_) if text_detector_service.pipeline else [],
                "explainability": "Feature Contribution Weights"
            },
            "face_deepfake_video_detector": {
                "engine": "ResNeXt50 + LSTM (20-frame sequence)",
                "task": "Face-manipulated/deepfake video screening",
                "checkpoint": str(settings.DEEPFAKE_VIDEO_MODEL_CHECKPOINT),
            },
            "video_detector": {
                "engine": "OpenCV Frame Sampler + EfficientNet-B0",
                "sampling_rate": f"{settings.VIDEO_FRAME_SAMPLE_RATE} fps",
                "max_frames": settings.MAX_VIDEO_FRAMES_TO_ANALYZE,
                "aggregation": "Conservative 60% Peak + 40% Mean Pooling"
            },
            "url_analyzer": {
                "heuristics": "Lexical analysis, punycode/IDN, deceptive subdomains, SSRF protection",
                "network_inspection": "Safe DNS and IP Range Filtering"
            }
        },
        active_environment=settings.ENVIRONMENT,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@router.post("/analyze/image", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_image(
    file: UploadFile = File(...),
    claimed_hash: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    safe_name = sanitize_filename(file.filename or "upload.jpg")
    content = await file.read()

    # Security: File validation
    is_valid, err_msg, mime = validate_image_file(content, safe_name, settings.MAX_IMAGE_FILE_SIZE_MB)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Provenance and Integrity
    prov_res = provenance_service.inspect_image_provenance(content)
    if claimed_hash:
        prov_res["hash_verification"] = provenance_service.verify_hash(content, claimed_hash)

    # ML Inference
    img_res = image_detector_service.predict(content)

    detector_results = {
        "image_detector": img_res,
        "provenance": prov_res
    }

    # Centralized Risk Engine
    response = risk_engine.evaluate(
        input_type="image",
        detector_results=detector_results,
        content_hash=prov_res.get("content_sha256"),
        source_reference=safe_name
    )

    # Save to database
    history_service.save_analysis(db, response, source_reference=safe_name)
    return response

@router.post("/analyze/video", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    safe_name = sanitize_filename(file.filename or "upload.mp4")
    content = await file.read()

    # Security: Video validation
    is_valid, err_msg, mime = validate_video_file(content, safe_name, settings.MAX_VIDEO_FILE_SIZE_MB)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    sha256_hash = provenance_service.compute_sha256(content)

    # Video extraction & frame inference
    vid_res = video_detector_service.analyze_video(content, safe_name)
    if vid_res.get("status") == "failed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=vid_res.get("error"))

    deepfake_res = deepfake_video_detector_service.predict_video_bytes(content, safe_name)
    detector_results = {
        "video_detector": vid_res,
        "deepfake_video_detector": deepfake_res,
        "provenance": {
            "content_sha256": sha256_hash,
            "container_format": mime,
            "methodology_note": "SHA-256 verifies digital bitstream integrity of the uploaded video container."
        }
    }

    response = risk_engine.evaluate(
        input_type="video",
        detector_results=detector_results,
        content_hash=sha256_hash,
        source_reference=safe_name
    )

    history_service.save_analysis(db, response, source_reference=safe_name)
    return response

@router.post("/analyze/text", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_text(
    payload: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    txt_res = text_detector_service.predict(payload.text)

    detector_results = {
        "text_detector": txt_res
    }

    # If an optional context URL is present, analyze it too
    if payload.context_url:
        url_res = url_analyzer_service.analyze_url(payload.context_url)
        detector_results["url_analyzer"] = url_res

    response = risk_engine.evaluate(
        input_type="text",
        detector_results=detector_results,
        source_reference=payload.text[:80] + ("..." if len(payload.text) > 80 else "")
    )

    history_service.save_analysis(db, response, source_reference=payload.text[:80])
    return response

@router.post("/analyze/url", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_url(
    payload: UrlAnalysisRequest,
    db: Session = Depends(get_db)
):
    url_res = url_analyzer_service.analyze_url(payload.url, payload.enable_network_checks)

    detector_results = {
        "url_analyzer": url_res
    }

    response = risk_engine.evaluate(
        input_type="url",
        detector_results=detector_results,
        source_reference=payload.url
    )

    history_service.save_analysis(db, response, source_reference=payload.url)
    return response

@router.post("/analyze/impersonation", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_impersonation(
    payload: ImpersonationAnalysisRequest,
    db: Session = Depends(get_db)
):
    # Cross-reference claimed entity with domain and message text
    detector_results = {}

    if payload.message_text:
        txt_res = text_detector_service.predict(payload.message_text)
        detector_results["text_detector"] = txt_res

    domain_mismatch = False
    impersonation_notes = []

    if payload.domain and payload.claimed_entity:
        low_claim = payload.claimed_entity.lower().replace(" ", "")
        low_domain = payload.domain.lower()
        # Verify if domain matches claimed organization
        if low_claim not in low_domain:
            domain_mismatch = True
            impersonation_notes.append(
                f"Mismatch detected: Claimed entity '{payload.claimed_entity}' is not aligned with origin domain '{payload.domain}'."
            )

    detector_results["impersonation_engine"] = {
        "claimed_entity": payload.claimed_entity,
        "profile_handle": payload.profile_handle,
        "domain": payload.domain,
        "domain_mismatch": domain_mismatch,
        "notes": impersonation_notes,
        "identity_claim_disclaimer": "MediaTrust analyzes inconsistency markers. It does not establish real-world identity from appearance alone."
    }

    response = risk_engine.evaluate(
        input_type="impersonation",
        detector_results=detector_results,
        source_reference=f"Claim: {payload.claimed_entity}"
    )

    history_service.save_analysis(db, response, source_reference=f"Claim: {payload.claimed_entity}")
    return response

@router.post("/analyze/page", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_page(
    payload: PageAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Multi-modal webpage inspection endpoint called by the browser extension."""
    detector_results = {}

    # 1. Analyze the page URL and a few visible link destinations lexically.
    # Page scans do lexical URL checks only; they do not resolve or fetch destinations.
    url_candidates = [payload.url]
    url_candidates.extend(
        link for link in payload.links[:5]
        if isinstance(link, str) and link.startswith(("http://", "https://"))
    )
    url_results = [url_analyzer_service.analyze_url(candidate, resolve_hostname=False) for candidate in url_candidates]
    url_res = max(url_results, key=lambda result: result.get("lexical_risk_score", 0))
    url_res["checked_visible_link_count"] = max(0, len(url_candidates) - 1)
    detector_results["url_analyzer"] = url_res

    # 2. Analyze visible page text snippet
    if payload.text_content:
        txt_res = text_detector_service.predict(payload.text_content)
        detector_results["text_detector"] = txt_res

    single_frame_rgb = None
    parsed_source = urlsplit(payload.url or "")
    source_host = (parsed_source.hostname or "").lower()
    source_path = parsed_source.path.lower()
    is_video_route = (
        source_host.endswith("instagram.com") and re.search(r"/(reel|reels|tv)/", source_path) is not None
    ) or (
        source_host.endswith(("youtube.com", "youtu.be")) and re.search(r"/(watch|shorts|live)/?", source_path) is not None
    ) or (
        source_host.endswith("tiktok.com") and "/video/" in source_path
    ) or (
        source_host.endswith("facebook.com") and re.search(r"/(reel|watch)/", source_path) is not None
    )
    is_video_context = bool(payload.video_context or payload.video_frame_data_urls or is_video_route)
    # A still sampled from a video must never be reinterpreted as a standalone image.
    if payload.frame_data_url:
        prefix = "data:image/jpeg;base64,"
        if not payload.frame_data_url.startswith(prefix):
            raise HTTPException(status_code=422, detail="Frame must be a JPEG data URL.")
        try:
            frame_bytes = base64.b64decode(payload.frame_data_url[len(prefix):], validate=True)
        except (ValueError, base64.binascii.Error):
            raise HTTPException(status_code=422, detail="Frame data is not valid base64.")
        if not frame_bytes or len(frame_bytes) > 512 * 1024:
            raise HTTPException(status_code=413, detail="Sampled frame exceeds the 512 KB limit.")
        valid, error, _mime = validate_image_file(frame_bytes, "sample.jpg", 1)
        if not valid:
            raise HTTPException(status_code=422, detail=error)
        try:
            single_frame_rgb = np.asarray(Image.open(io.BytesIO(frame_bytes)).convert("RGB"))
        except Exception:
            pass
        if not is_video_context:
            detector_results["image_detector"] = image_detector_service.predict(frame_bytes)

    if payload.video_frame_data_urls:
        if len(payload.video_frame_data_urls) > 20:
            raise HTTPException(status_code=413, detail="At most 20 video frames are accepted.")
        frame_bytes_list = []
        frames_rgb = []
        total_encoded_chars = 0
        for encoded_frame in payload.video_frame_data_urls:
            prefix = "data:image/jpeg;base64,"
            if not encoded_frame.startswith(prefix):
                raise HTTPException(status_code=422, detail="Every sampled video frame must be a JPEG data URL.")
            total_encoded_chars += len(encoded_frame)
            if len(encoded_frame) > 180000 or total_encoded_chars > 2500000:
                raise HTTPException(status_code=413, detail="Video frame sequence exceeds the request size limit.")
            try:
                raw = base64.b64decode(encoded_frame[len(prefix):], validate=True)
            except (ValueError, base64.binascii.Error):
                raise HTTPException(status_code=422, detail="A sampled video frame is not valid base64.")
            valid, error, _mime = validate_image_file(raw, "reel-frame.jpg", 1)
            if not valid:
                raise HTTPException(status_code=422, detail=f"Invalid sampled video frame: {error}")
            try:
                rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
            except Exception:
                raise HTTPException(status_code=422, detail="A sampled video frame could not be decoded.")
            frame_bytes_list.append(raw)
            frames_rgb.append(rgb)

        score_result = image_detector_service.predict_ai_scores(frame_bytes_list)
        scores = score_result.get("scores", []) if score_result.get("status") == "completed" else []
        frame_count = len(scores)
        if frame_count < settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT:
            detector_results["video_detector"] = {
                "status": "inconclusive",
                "error": f"Need at least {settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT} sampled frames for a reel AI alert; received {frame_count}. No single-frame verdict was made.",
                "frames_analyzed": frame_count,
                "ai_decision_threshold": settings.VIDEO_AI_ALERT_THRESHOLD,
                "ai_alert_enabled": settings.VIDEO_AI_ALERTS_ENABLED,
                "model_version": "EfficientNet-B0-ReelFramePool-v1",
            }
        elif scores:
            p85 = float(np.percentile(scores, 85))
            mean_score = float(np.mean(scores))
            detector_results["video_detector"] = {
                "status": "completed",
                "frames_analyzed": frame_count,
                "aggregate_ai_score": round(0.60 * p85 + 0.40 * mean_score, 4),
                "peak_frame_score": round(max(scores), 4),
                "mean_frame_score": round(mean_score, 4),
                "ai_decision_threshold": settings.VIDEO_AI_ALERT_THRESHOLD,
                "ai_alert_enabled": settings.VIDEO_AI_ALERTS_ENABLED,
                "model_version": "EfficientNet-B0-ReelFramePool-v1",
                "aggregation_methodology": "60% 85th-percentile frame score + 40% mean frame score",
                "limitations": ["Frame-level generative-image clues are not temporal video forensics and can miss face swaps or AI video outside the training distribution."],
            }
        detector_results["deepfake_video_detector"] = deepfake_video_detector_service.predict_frames(frames_rgb)
    elif is_video_context:
        detector_results["video_detector"] = {
            "status": "inconclusive",
            "error": f"A reel AI alert needs at least {settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT} sampled frames. Only a still frame was available.",
            "frames_analyzed": 0,
            "ai_decision_threshold": settings.VIDEO_AI_ALERT_THRESHOLD,
            "ai_alert_enabled": settings.VIDEO_AI_ALERTS_ENABLED,
            "model_version": "EfficientNet-B0-ReelFramePool-v1",
        }
        detector_results["deepfake_video_detector"] = deepfake_video_detector_service.predict_frames([single_frame_rgb] if single_frame_rgb is not None else [])
    elif payload.frame_data_url:
        detector_results["deepfake_video_detector"] = deepfake_video_detector_service.predict_frames([single_frame_rgb] if single_frame_rgb is not None else [])

    response = risk_engine.evaluate(
        input_type="page",
        detector_results=detector_results,
        source_reference=payload.url
    )

    history_service.save_analysis(db, response, source_reference=payload.url)
    return response

@router.get("/analyses", tags=["History"])
def list_analyses(
    input_type: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    records = history_service.get_analyses(db, input_type, risk, limit, offset)
    return [
        {
            "analysis_id": r.id,
            "input_type": r.input_type,
            "status": r.status,
            "overall_risk": r.overall_risk,
            "risk_score": r.risk_score,
            "classification_tag": getattr(r, "classification_tag", "normal"),
            "classification_label": getattr(r, "classification_label", "No strong threat indicators in scanned content"),
            "summary": r.summary,
            "source_reference": r.source_reference,
            "created_at": r.created_at.isoformat() + "Z"
        }
        for r in records
    ]

@router.get("/analyses/{analysis_id}", tags=["History"])
def get_analysis_detail(analysis_id: str, db: Session = Depends(get_db)):
    record = history_service.get_analysis_by_id(db, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    return {
        "analysis_id": record.id,
        "input_type": record.input_type,
        "status": record.status,
        "overall_risk": record.overall_risk,
        "risk_score": record.risk_score,
        "score_type": record.score_type,
        "classification_tag": getattr(record, "classification_tag", "normal"),
        "classification_label": getattr(record, "classification_label", "No strong threat indicators in scanned content"),
        "confidence": record.confidence,
        "summary": record.summary,
        "content_hash": record.content_hash,
        "source_reference": record.source_reference,
        "findings": record.findings,
        "detector_results": record.detector_results,
        "limitations": record.limitations,
        "recommended_actions": record.recommended_actions,
        "model_versions": record.model_versions,
        "created_at": record.created_at.isoformat() + "Z"
    }

@router.delete("/analyses/{analysis_id}", tags=["History"])
def delete_analysis_record(analysis_id: str, db: Session = Depends(get_db)):
    success = history_service.delete_analysis(db, analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return {"status": "deleted", "analysis_id": analysis_id}

@router.get("/analytics/summary", tags=["Analytics"])
def get_analytics(db: Session = Depends(get_db)):
    return history_service.get_analytics_summary(db)

@router.get("/models", tags=["Models"])
def get_model_registry():
    return {
        "image_detector": {
            "name": "EfficientNet-B0 Deepfake & AI Image Classifier",
            "version": "1.0.0",
            "type": "Convolutional Neural Network (Transfer Learning)",
            "pretrained_weights": "ImageNet-1K initialization",
            "head": "Binary Classifier Head (Real vs AI-Generated) with Dropout",
            "explainability": "Grad-CAM Activation Visualizer",
            "input_resolution": "224x224 RGB",
            "status": "active" if image_detector_service.model_loaded else "unavailable"
        },
        "text_detector": {
            "name": "Supervised TF-IDF Security Intent Classifier",
            "version": "1.0.0",
            "type": "TF-IDF Vectorizer + Multinomial Logistic Regression",
            "classes": list(text_detector_service.pipeline.named_steps["classifier"].classes_) if text_detector_service.pipeline else [],
            "explainability": "Token Feature Contribution Coefficients",
            "status": ("demo" if text_detector_service.model_version.startswith("text-seed-demo") else "active") if text_detector_service.model_loaded else "unavailable",
            "model_version": text_detector_service.model_version,
            "evaluation_scope": getattr(text_detector_service.pipeline, "mediatrust_evaluation_scope_", "demo_or_unverified") if text_detector_service.pipeline else "unavailable"
        },
        "face_deepfake_video_detector": {
            "name": "ResNeXt50 + LSTM Face Deepfake Detector",
            "version": "ResNeXt50-LSTM-DFDC-CelebDF-v1",
            "type": "20-frame ResNeXt50 spatial encoder + LSTM temporal classifier",
            "status": "active" if deepfake_video_detector_service.model_loaded else "unavailable",
            "scope": "Face manipulation screening; not general AI-video generation detection",
        },
        "video_detector": {
            "name": "Temporal Video Frame Sampler & Anomaly Aggregator",
            "version": "1.0.0",
            "type": "OpenCV Multi-Frame Pipeline",
            "aggregation": "Conservative 60% 85th-Percentile Anomaly + 40% Sequence Mean",
            "status": "active" if image_detector_service.model_loaded else "unavailable"
        },
        "url_analyzer": {
            "name": "Lexical & Heuristic Domain Risk Engine",
            "version": "1.0.0",
            "type": "Structural Rule Engine with SSRF Hardening",
            "status": "active"
        }
    }

@router.get("/models/{model_name}/metrics", tags=["Models"])
def get_model_metrics(model_name: str):
    report_files = {
        "image_detector": settings.MODELS_DIR / "image_metrics.json",
        "text_detector": settings.MODELS_DIR / "text_classifier_external_metrics.json",
    }
    if model_name not in report_files:
        raise HTTPException(status_code=404, detail=f"Metrics for model '{model_name}' not available.")
    report_path = report_files[model_name]
    if not report_path.is_file():
        return {
            "model": model_name,
            "status": "not_evaluated",
            "evaluation_note": "No reproducible evaluation report is installed. Train a model and review its held-out report."
        }
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="Model evaluation report could not be read.")
    if model_name == "image_detector":
        per_class = report.get("per_class", {})
        ai = per_class.get("ai_generated", {})
        matrix = report.get("confusion_matrix", [[0, 0], [0, 0]])
        return {
            "model": "EfficientNet-B0 image classifier",
            "status": "evaluated",
            "evaluation_scope": report.get("evaluation_scope"),
            "test_rows": report.get("test_rows"),
            "accuracy": per_class.get("accuracy"),
            "precision": ai.get("precision"),
            "recall": ai.get("recall"),
            "roc_auc": report.get("roc_auc"),
            "confusion_matrix": {
                "true_negative": matrix[0][0], "false_positive": matrix[0][1],
                "false_negative": matrix[1][0], "true_positive": matrix[1][1]
            },
            "selected_ai_threshold": report.get("selected_ai_threshold"),
            "evaluation_note": report.get("warning")
        }
    test = report.get("test", {})
    raw_classes = test.get("per_class", {})
    per_class = {
        name: values for name, values in raw_classes.items()
        if isinstance(values, dict) and name not in ("macro avg", "weighted avg")
    }
    return {
        "model": "TF-IDF Logistic Regression text classifier",
        "status": "evaluated",
        "evaluation_scope": report.get("evaluation_scope"),
        "test_rows": test.get("rows"),
        "macro_f1": test.get("macro_f1"),
        "weighted_f1": raw_classes.get("weighted avg", {}).get("f1-score"),
        "per_class_metrics": {
            name: {"precision": values.get("precision"), "recall": values.get("recall"), "f1": values.get("f1-score")}
            for name, values in per_class.items()
        },
        "evaluation_note": report.get("warning")
    }

@router.post("/integrity/hash", tags=["Integrity"])
async def compute_file_hash(file: UploadFile = File(...)):
    content = await file.read()
    digest = provenance_service.compute_sha256(content)
    return {
        "filename": sanitize_filename(file.filename or "file"),
        "sha256": digest,
        "byte_size": len(content),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

@router.post("/integrity/verify", tags=["Integrity"])
def verify_hash(payload: IntegrityVerifyRequest):
    if not payload.file_content_hash:
        raise HTTPException(status_code=400, detail="Missing file_content_hash for verification.")
    res = provenance_service.verify_hash(payload.file_content_hash.encode(), payload.claimed_hash)
    return res
