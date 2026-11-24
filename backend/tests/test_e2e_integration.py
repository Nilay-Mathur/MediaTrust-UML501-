import os
import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_system_integration():
    print("Testing health check...")
    h = client.get("/api/v1/health")
    assert h.status_code == 200

    print("Testing system status...")
    s = client.get("/api/v1/system/status")
    assert s.status_code == 200
    assert s.json()["status"] == "operational"
    assert isinstance(s.json()["models_loaded"]["image_detector"], bool)

    print("Testing text analysis with scam financial lure...")
    t = client.post("/api/v1/analyze/text", json={
        "text": "CONGRATULATIONS! You have won $1,000,000 in the International Lottery! Send your bank details immediately to claim."
    })
    assert t.status_code == 200
    res_t = t.json()
    assert res_t["overall_risk"] in ("moderate", "high", "critical")
    assert res_t["detector_results"]["text_detector"]["predicted_category"] == "scam_fraud"

    print("Testing URL analysis with deceptive brand subdomain...")
    u = client.post("/api/v1/analyze/url", json={
        "url": "http://chase.com.security-account-portal.xyz/login"
    })
    assert u.status_code == 200
    res_u = u.json()
    assert res_u["risk_score"] >= 60

    print("Testing page analysis (extension flow)...")
    p = client.post("/api/v1/analyze/page", json={
        "url": "http://instagram.com/reel/123",
        "page_title": "Urgent Crypto Bonus Reel",
        "text_content": "Guaranteed 20% daily return! Send Bitcoin now to our VIP wallet address.",
        "video_urls": ["http://cdn.instagram.com/video123.mp4"]
    })
    assert p.status_code == 200
    res_p = p.json()
    assert res_p["overall_risk"] in ("moderate", "high", "critical")

    print("All End-to-End Integration Tests Passed Successfully!")

if __name__ == "__main__":
    test_full_system_integration()
