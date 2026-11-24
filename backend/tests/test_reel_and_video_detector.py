import io
import base64
import numpy as np
from PIL import Image

def test_reel_page_analysis_scam(client):
    # Simulate a suspicious crypto scam reel with deceptive link and coercive text
    payload = {
        "url": "https://instagram.com/reel/C123456",
        "page_title": "VIP Crypto Airdrop Reel",
        "text_content": "URGENT: Invest $100 and receive guaranteed 50% daily return! Send Bitcoin to our VIP Telegram wallet immediately. Limited to first 10 users! Click link: http://crypto-doubler-free-claim.xyz",
        "links": ["http://crypto-doubler-free-claim.xyz"]
    }
    response = client.post("/api/v1/analyze/page", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] in ("high", "critical")
    assert data["classification_tag"] in ("scam", "suspicious")
    assert data["risk_score"] >= 60
    assert any("scam" in f["description"].lower() or "threat" in f["description"].lower() for f in data["findings"])

def test_reel_page_analysis_benign(client):
    # Simulate a clean nature / travel reel
    payload = {
        "url": "https://instagram.com/reel/C987654",
        "page_title": "Hiking the Swiss Alps Vlog",
        "text_content": "Exploring the beautiful autumn trails in the Swiss Alps! The morning mist and golden larch trees were breathtaking. Have a wonderful weekend everyone! #nature #travel",
        "links": []
    }
    response = client.post("/api/v1/analyze/page", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "low"
    assert data["classification_tag"] == "normal"
    assert data["risk_score"] < 30

def test_reel_page_analysis_with_frame(client):
    # Generate a sample frame
    img = Image.new("RGB", (224, 224), color=(140, 160, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    frame_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    payload = {
        "url": "https://instagram.com/reel/C555555",
        "page_title": "Sample Reel",
        "text_content": "Just sharing today's quick cooking recipe for fresh pasta.",
        "frame_data_url": frame_b64
    }
    response = client.post("/api/v1/analyze/page", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "video_detector" in data["detector_results"]
    assert "image_detector" in data["detector_results"]
