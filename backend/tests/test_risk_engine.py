from app.ml.risk_engine.engine import risk_engine

def test_risk_engine_critical_threshold():
    detector_results = {
        "text_detector": {
            "status": "completed",
            "predicted_category": "phishing_credential_theft",
            "confidence": 0.95,
            "threat_indicators": [
                {"indicator": "Urgency & Coercion", "matched_sample": "immediate", "explanation": "Urgent demand"}
            ]
        },
        "url_analyzer": {
            "status": "completed",
            "lexical_risk_score": 85,
            "findings": [
                {"rule": "DECEPTIVE_BRAND_IMPERSONATION", "severity": "critical", "description": "Brand spoofing", "evidence": "paypal.xyz"}
            ]
        }
    }
    response = risk_engine.evaluate(input_type="text", detector_results=detector_results)
    assert response.overall_risk in ("high", "critical")
    assert response.risk_score >= 70
    assert response.score_type == "heuristic_risk_score"
    assert len(response.findings) >= 2

def test_risk_engine_low_risk():
    detector_results = {
        "text_detector": {
            "status": "completed",
            "predicted_category": "benign",
            "confidence": 0.98
        }
    }
    response = risk_engine.evaluate(input_type="text", detector_results=detector_results)
    assert response.overall_risk == "low"
    assert response.risk_score < 30
