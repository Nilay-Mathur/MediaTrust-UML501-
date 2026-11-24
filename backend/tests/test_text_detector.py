from app.ml.text_detector.service import text_detector_service

def test_text_detector_phishing():
    res = text_detector_service.predict("URGENT: Your Chase Bank account is locked. Verify password now.")
    assert res["status"] == "completed"
    assert res["predicted_category"] in ("phishing_credential_theft", "scam_fraud")
    assert res["confidence"] > 0.35
    assert res["confidence"] == max(res["probabilities"].values())
    assert len(res["top_contributing_features"]) > 0

def test_text_detector_benign():
    res = text_detector_service.predict("Hey Sarah, let's meet for lunch at the cafeteria tomorrow at noon.")
    assert res["status"] == "completed"
    assert res["predicted_category"] == "benign"
    assert "probabilities" in res
