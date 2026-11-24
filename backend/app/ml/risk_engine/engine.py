import uuid
import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.analysis import AnalysisResponse, EvidenceItem

class CentralizedRiskEngine:
    def __init__(self):
        self.threshold_low = settings.RISK_THRESHOLD_LOW        # 30
        self.threshold_mod = settings.RISK_THRESHOLD_MODERATE   # 60
        self.threshold_high = settings.RISK_THRESHOLD_HIGH      # 85

    def evaluate(
        self,
        input_type: str,
        detector_results: Dict[str, Any],
        content_hash: Optional[str] = None,
        source_reference: Optional[str] = None
    ) -> AnalysisResponse:
        """
        Synthesizes multimodal findings, normalizes evidence, applies risk policy,
        and produces a unified, explainable audit assessment.
        """
        analysis_id = f"mt-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        findings: List[EvidenceItem] = []
        limitations: List[str] = []
        recommended_actions: List[str] = []
        model_versions: Dict[str, str] = {}
        risk_components: List[int] = []

        # -------------------------------------------------------------
        # 1. Evaluate Image Detector Results
        # -------------------------------------------------------------
        if "image_detector" in detector_results:
            img_res = detector_results["image_detector"]
            model_versions["image_detector"] = img_res.get("model_version", "EfficientNet-B0-v1.0")

            if img_res.get("status") == "completed":
                ai_score = img_res.get("ai_generated_score", 0.0)
                prediction = img_res.get("prediction", "real_image")
                confidence = img_res.get("confidence", 0.0)

                ai_threshold = max(float(img_res.get("ai_decision_threshold", 0.55)), 0.85)
                is_video_sample = detector_results.get("video_detector", {}).get("status") == "completed"
                if is_video_sample:
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-img-{uuid.uuid4().hex[:6]}",
                        category="media_authenticity",
                        description=f"Single sampled frame score ({ai_score*100:.1f}%) is informational only; this reel is judged using the pooled video score and its 85% alert cutoff.",
                        source_detector="image_detector",
                        severity="info",
                        verification_status="predicted",
                        supporting_data={"ai_score": ai_score, "decision_threshold": ai_threshold, "reel_frame_only": True}
                    ))
                elif ai_score >= ai_threshold:
                    sev = "critical" if ai_score >= 0.85 else "high"
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-img-{uuid.uuid4().hex[:6]}",
                        category="ai_generated_media",
                        description=f"AI-generated synthetic image detected ({ai_score*100:.1f}% confidence, threshold {ai_threshold*100:.1f}%). Generative texture artifacts observed.",
                        source_detector="image_detector",
                        severity=sev,
                        verification_status="predicted",
                        supporting_data={"ai_score": ai_score, "confidence": confidence, "decision_threshold": ai_threshold, "has_gradcam": bool(img_res.get("grad_cam_overlay"))}
                    ))
                else:
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-img-{uuid.uuid4().hex[:6]}",
                        category="media_authenticity",
                        description=f"Authentic visual characteristics ({img_res.get('real_score', 0.0)*100:.1f}% authentic score; {ai_score*100:.1f}% synthetic).",
                        source_detector="image_detector",
                        severity="info",
                        verification_status="predicted",
                        supporting_data={"real_score": img_res.get("real_score", 0.0)}
                    ))

                if "limitations" in img_res:
                    limitations.extend(img_res["limitations"])
            elif img_res.get("status") == "unavailable":
                limitations.append("Image detector was unavailable during analysis. Risk calculation proceeded without it.")

        # -------------------------------------------------------------
        # 2. Evaluate Video Detector Results
        # -------------------------------------------------------------
        if "video_detector" in detector_results:
            vid_res = detector_results["video_detector"]
            model_versions["video_detector"] = vid_res.get("model_version", "EfficientNet-B0-VideoSampler-v1.0")

            if vid_res.get("status") == "completed":
                agg_score = vid_res.get("aggregate_ai_score", 0.0)
                peak_score = vid_res.get("peak_frame_score", 0.0)
                frames_count = vid_res.get("frames_analyzed", 0)

                ai_threshold = max(float(vid_res.get("ai_decision_threshold", settings.VIDEO_AI_ALERT_THRESHOLD)), settings.VIDEO_AI_ALERT_THRESHOLD)
                ai_alert_enabled = bool(vid_res.get("ai_alert_enabled", settings.VIDEO_AI_ALERTS_ENABLED))
                if ai_alert_enabled and frames_count >= settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT and agg_score >= ai_threshold:
                    sev = "critical" if agg_score >= 0.80 else "high"
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-vid-{uuid.uuid4().hex[:6]}",
                        category="video_frame_anomaly",
                        description=f"AI-generated video / reel detected: sampled frames scored {agg_score*100:.1f}% synthetic probability (peak frame {peak_score*100:.1f}%, threshold {ai_threshold*100:.1f}%).",
                        source_detector="video_detector",
                        severity=sev,
                        verification_status="predicted",
                        supporting_data={"ai_score": agg_score, "aggregate_score": agg_score, "peak_frame_score": peak_score, "frames_analyzed": frames_count, "decision_threshold": ai_threshold}
                    ))
                else:
                    insufficient_frames = frames_count < settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-vid-{uuid.uuid4().hex[:6]}",
                        category="video_consistency",
                        description=(
                            f"No AI verdict: only {frames_count} frames were sampled; at least {settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT} are required."
                            if insufficient_frames else
                            f"No AI alert: pooled visual score was {agg_score*100:.1f}% across {frames_count} sampled frames, below the {ai_threshold*100:.1f}% threshold."
                        ),
                        source_detector="video_detector",
                        severity="info",
                        verification_status="predicted",
                        supporting_data={"aggregate_score": agg_score, "peak_frame_score": peak_score, "frames_analyzed": frames_count, "decision_threshold": ai_threshold}
                    ))

                if "limitations" in vid_res:
                    limitations.extend(vid_res["limitations"])
            elif vid_res.get("status") == "inconclusive":
                limitations.append(vid_res.get("error", "Not enough video frames were sampled for an AI verdict."))

        # -------------------------------------------------------------
        # 3. Evaluate face-deepfake sequence model
        # -------------------------------------------------------------
        if "deepfake_video_detector" in detector_results:
            deepfake_res = detector_results["deepfake_video_detector"]
            model_versions["face_deepfake_video_detector"] = deepfake_res.get("model_version", "ResNeXt50-LSTM-v1")
            if deepfake_res.get("status") == "completed":
                fake_score = float(deepfake_res.get("fake_probability", 0.0))
                threshold = max(float(deepfake_res.get("decision_threshold", 0.5)), settings.FACE_DEEPFAKE_ALERT_THRESHOLD)
                frames_count = int(deepfake_res.get("frames_analyzed", 0))
                face_detected_count = int(deepfake_res.get("face_frames_detected", 0))

                if fake_score >= threshold and face_detected_count >= 10 and deepfake_res.get("face_crops_applied") is True:
                    sev = "critical" if fake_score >= 0.80 else "high"
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-df-{uuid.uuid4().hex[:6]}",
                        category="face_deepfake_signal",
                        description=f"Face-manipulated deepfake video detected ({fake_score*100:.1f}% probability across {face_detected_count} face frames). Spatial-temporal facial inconsistencies observed.",
                        source_detector="deepfake_video_detector",
                        severity=sev,
                        verification_status="predicted",
                        supporting_data={"fake_probability": fake_score, "deepfake_score": fake_score, "real_probability": deepfake_res.get("real_probability", 0.0), "decision_threshold": threshold, "frames_analyzed": frames_count, "face_crops_applied": deepfake_res.get("face_crops_applied", False), "face_frames_detected": face_detected_count}
                    ))
                else:
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-df-{uuid.uuid4().hex[:6]}",
                        category="face_deepfake_screening",
                        description=f"Facial motion analysis consistent with authentic capture ({fake_score*100:.1f}% deepfake probability across {face_detected_count} face frames).",
                        source_detector="deepfake_video_detector",
                        severity="info",
                        verification_status="predicted",
                        supporting_data={"fake_probability": fake_score, "deepfake_score": fake_score, "real_probability": deepfake_res.get("real_probability", 0.0), "decision_threshold": threshold, "frames_analyzed": frames_count, "face_crops_applied": deepfake_res.get("face_crops_applied", False), "face_frames_detected": face_detected_count}
                    ))
                limitations.extend(deepfake_res.get("limitations", []))
            elif deepfake_res.get("error"):
                limitations.append(deepfake_res.get("error"))

        # -------------------------------------------------------------
        # 4. Evaluate Text Detector Results
        # -------------------------------------------------------------
        if "text_detector" in detector_results:
            txt_res = detector_results["text_detector"]
            model_versions["text_detector"] = txt_res.get("model_version", "TFIDF-LogisticRegression-v1.0")

            if txt_res.get("status") == "completed":
                cat = txt_res.get("predicted_category", "benign")
                conf = txt_res.get("confidence", 0.0)

                if cat in ("scam_fraud", "phishing_credential_theft", "impersonation") and conf >= settings.TEXT_THREAT_ALERT_THRESHOLD:
                    txt_risk = int(conf * 100)
                    risk_components.append(txt_risk)

                    sev = "critical" if conf >= 0.80 else ("high" if conf >= 0.60 else "moderate")
                    cat_labels = {
                        "scam_fraud": "Scam & Financial Fraud",
                        "phishing_credential_theft": "Phishing & Credential Theft",
                        "impersonation": "Impersonation & Social Engineering"
                    }
                    cat_name = cat_labels.get(cat, cat)
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-txt-{uuid.uuid4().hex[:6]}",
                        category=f"text_{cat}",
                        description=f"{cat_name} detected ({conf*100:.1f}% model confidence). Text aligns with known threat signatures.",
                        source_detector="text_detector",
                        severity=sev,
                        verification_status="predicted",
                        supporting_data={"category": cat, "confidence": conf, "top_features": txt_res.get("top_contributing_features", [])}
                    ))
                elif cat in ("scam_fraud", "phishing_credential_theft", "impersonation"):
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-txt-{uuid.uuid4().hex[:6]}",
                        category="text_model_unverified",
                        description=f"Unverified text-model signal: predicted {cat.replace('_', ' ')} at {conf*100:.1f}% confidence, below the {settings.TEXT_THREAT_ALERT_THRESHOLD*100:.0f}% scam-alert threshold. This was not counted as a scam finding.",
                        source_detector="text_detector",
                        severity="info",
                        verification_status="predicted",
                        supporting_data={"category": cat, "confidence": conf, "alert_threshold": settings.TEXT_THREAT_ALERT_THRESHOLD, "top_features": txt_res.get("top_contributing_features", [])}
                    ))
                else:
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-txt-{uuid.uuid4().hex[:6]}",
                        category="text_benign",
                        description=f"Text language aligns with standard benign correspondence ({conf*100:.1f}% confidence).",
                        source_detector="text_detector",
                        severity="info",
                        verification_status="predicted"
                    ))

                # Include threat indicator rules
                for ind in txt_res.get("threat_indicators", []):
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-ind-{uuid.uuid4().hex[:6]}",
                        category="heuristic_text_trigger",
                        description=f"{ind['indicator']}: {ind['explanation']} (Matched: '{ind['matched_sample']}')",
                        source_detector="text_detector",
                        severity="moderate",
                        verification_status="observed"
                    ))
                    risk_components.append(60)

                if "limitations" in txt_res:
                    limitations.extend(txt_res["limitations"])

        # -------------------------------------------------------------
        # 4. Evaluate URL Analyzer Results
        # -------------------------------------------------------------
        if "url_analyzer" in detector_results:
            url_res = detector_results["url_analyzer"]
            model_versions["url_analyzer"] = url_res.get("model_version", "Heuristic-Lexical-URL-v1.0")

            if url_res.get("status") == "completed":
                lex_score = url_res.get("lexical_risk_score", 0)
                risk_components.append(lex_score)

                for f in url_res.get("findings", []):
                    findings.append(EvidenceItem(
                        evidence_id=f"ev-url-{uuid.uuid4().hex[:6]}",
                        category="url_security",
                        description=f"{f['rule']}: {f['description']} ({f['evidence']})",
                        source_detector="url_analyzer",
                        severity=f["severity"],
                        verification_status="observed"
                    ))

        # -------------------------------------------------------------
        # 5. Evaluate Provenance and Integrity
        # -------------------------------------------------------------
        if "provenance" in detector_results:
            prov_res = detector_results["provenance"]
            if prov_res.get("detected_ai_signatures"):
                findings.append(EvidenceItem(
                    evidence_id=f"ev-prov-{uuid.uuid4().hex[:6]}",
                    category="provenance_metadata",
                    description=f"Generative software signature found in EXIF tags: {', '.join(prov_res['detected_ai_signatures'])}",
                    source_detector="provenance",
                    severity="high",
                    verification_status="observed",
                    supporting_data={"signatures": prov_res["detected_ai_signatures"]}
                ))
            elif prov_res.get("has_camera_hardware_tags"):
                findings.append(EvidenceItem(
                    evidence_id=f"ev-prov-{uuid.uuid4().hex[:6]}",
                    category="provenance_metadata",
                    description=f"Physical camera hardware metadata preserved (Camera: {prov_res.get('metadata_summary', {}).get('Make', 'Unknown')}).",
                    source_detector="provenance",
                    severity="info",
                    verification_status="observed"
                ))

        # -------------------------------------------------------------
        # 6. Aggregate Heuristic Risk Score & Category
        # -------------------------------------------------------------
        if not risk_components:
            overall_score = 0
            overall_risk = "low"
            status = "completed" if detector_results else "inconclusive"
            summary = "No scam or phishing indicators were found. AI-media screening results are reported separately."
        else:
            # Policy-based aggregation:
            # The highest individual severity signal establishes the baseline danger ceiling,
            # while the average of active detectors adjusts the overall score.
            max_risk = max(risk_components)
            avg_risk = sum(risk_components) / len(risk_components)
            # 65% weight to max risk factor, 35% to average across components
            overall_score = int(round(0.65 * max_risk + 0.35 * avg_risk))
            overall_score = max(0, min(100, overall_score))
            status = "completed"

            if overall_score >= self.threshold_high:
                overall_risk = "critical"
                summary = "Critical threat signals detected across multiple security indicators. Exercise extreme caution."
                recommended_actions = [
                    "Do not click associated links, open attachments, or input passwords.",
                    "Do not transfer money or authorize cryptocurrency transactions.",
                    "Report the account or URL to platform security administrators.",
                    "Verify the communication independently through known official channels."
                ]
            elif overall_score >= self.threshold_mod:
                overall_risk = "high"
                summary = "High risk: concrete scam, phishing, or suspicious-link evidence observed."
                recommended_actions = [
                    "Treat the content with skepticism; do not comply with urgency demands.",
                    "Inspect the sender's verified domain and check for character spoofing.",
                    "Look for secondary confirmation before acting on requests."
                ]
            elif overall_score >= self.threshold_low:
                overall_risk = "moderate"
                summary = "Moderate risk: Content exhibits minor suspicious traits or inconclusive indicators."
                recommended_actions = [
                    "Review findings details and check whether context justifies urgent language.",
                    "Ensure you are browsing on the official destination domain."
                ]
            else:
                overall_risk = "low"
                summary = "Low risk: No strong scam or phishing evidence detected in the available checks."
                recommended_actions = [
                    "No immediate red flags detected. Maintain standard digital hygiene."
                ]

        # Determine specific classification category (AI, Scam, Impersonation, Normal)
        img_ai_score = detector_results.get("image_detector", {}).get("ai_generated_score", 0.0)
        img_threshold = max(float(detector_results.get("image_detector", {}).get("ai_decision_threshold", 0.55)), 0.85)
        has_img_alert = detector_results.get("image_detector", {}).get("status") == "completed" and detector_results.get("video_detector", {}).get("status") != "completed" and img_ai_score >= img_threshold

        vid_ai_score = detector_results.get("video_detector", {}).get("aggregate_ai_score", 0.0)
        vid_peak_score = detector_results.get("video_detector", {}).get("peak_frame_score", 0.0)
        vid_threshold = max(float(detector_results.get("video_detector", {}).get("ai_decision_threshold", settings.VIDEO_AI_ALERT_THRESHOLD)), settings.VIDEO_AI_ALERT_THRESHOLD)
        video_alert_enabled = bool(detector_results.get("video_detector", {}).get("ai_alert_enabled", settings.VIDEO_AI_ALERTS_ENABLED))
        has_vid_alert = detector_results.get("video_detector", {}).get("status") == "completed" and int(detector_results.get("video_detector", {}).get("frames_analyzed", 0)) >= settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT and video_alert_enabled and vid_ai_score >= vid_threshold

        df_score = float(detector_results.get("deepfake_video_detector", {}).get("fake_probability", 0.0))
        df_result = detector_results.get("deepfake_video_detector", {})
        df_threshold = max(float(df_result.get("decision_threshold", 0.5)), settings.FACE_DEEPFAKE_ALERT_THRESHOLD)
        has_df_alert = df_result.get("status") == "completed" and df_score >= df_threshold and int(df_result.get("face_frames_detected", 0)) >= 10 and df_result.get("face_crops_applied") is True

        txt_cat = detector_results.get("text_detector", {}).get("predicted_category", "")
        txt_conf = float(detector_results.get("text_detector", {}).get("confidence", 0.0))
        impersonation_mismatch = detector_results.get("impersonation_engine", {}).get("domain_mismatch", False)

        if has_df_alert:
            classification_tag = "ai_generated"
            classification_label = f"Deepfake Video Detected ({df_score*100:.1f}%)"
        elif has_vid_alert or has_img_alert:
            classification_tag = "ai_generated"
            ai_score_val = vid_ai_score if has_vid_alert else img_ai_score
            classification_label = f"AI-Generated Media Detected ({ai_score_val*100:.1f}%)"
        elif txt_cat == "scam_fraud" and txt_conf >= settings.TEXT_THREAT_ALERT_THRESHOLD:
            classification_tag = "scam"
            classification_label = f"Potential Scam Detected ({txt_conf*100:.1f}%)"
        elif txt_cat == "phishing_credential_theft" and txt_conf >= settings.TEXT_THREAT_ALERT_THRESHOLD:
            classification_tag = "scam"
            classification_label = f"Phishing / Credential Theft Detected ({txt_conf*100:.1f}%)"
        elif (txt_cat == "impersonation" and txt_conf >= settings.TEXT_THREAT_ALERT_THRESHOLD) or impersonation_mismatch:
            classification_tag = "impersonation"
            classification_label = "Possible Impersonation Detected"
        elif overall_risk == "low":
            classification_tag = "normal"
            classification_label = "Clean Content: No Threat Detected"
        else:
            classification_tag = "suspicious"
            classification_label = "Suspicious Content"

        # De-duplicate limitations
        unique_limitations = list(dict.fromkeys(limitations))
        if not unique_limitations:
            unique_limitations = [
                "Assessment is based solely on inspected digital artifacts and trained baseline distributions.",
                "Adversarial evasion, high-grade deepfakes, and novel scam scripts may not trigger current heuristics."
            ]

        return AnalysisResponse(
            analysis_id=analysis_id,
            input_type=input_type,
            status=status,
            overall_risk=overall_risk,
            risk_score=overall_score,
            score_type="heuristic_risk_score",
            classification_tag=classification_tag,
            classification_label=classification_label,
            confidence=None,  # Heuristic score is not a single calibrated probability
            summary=summary,
            content_hash=content_hash,
            findings=findings,
            detector_results=detector_results,
            limitations=unique_limitations,
            recommended_actions=recommended_actions,
            model_versions=model_versions,
            timestamp=timestamp
        )

risk_engine = CentralizedRiskEngine()
