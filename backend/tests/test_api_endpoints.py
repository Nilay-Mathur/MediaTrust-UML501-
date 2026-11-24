import io
from PIL import Image

def test_api_text_analysis(client):
    payload = {"text": "URGENT: Verify your account password immediately to avoid suspension."}
    response = client.post("/api/v1/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert data["input_type"] == "text"
    assert data["overall_risk"] in ("moderate", "high", "critical")

def test_api_url_analysis(client):
    payload = {"url": "http://netflix-verify-billing.xyz/signin", "enable_network_checks": False}
    response = client.post("/api/v1/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["input_type"] == "url"
    assert data["risk_score"] > 30

def test_api_image_analysis(client):
    # Generate test image in memory
    img = Image.new("RGB", (224, 224), color=(120, 150, 180))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/v1/analyze/image",
        files={"file": ("test_photo.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["input_type"] == "image"
    assert "image_detector" in data["detector_results"]
    assert "provenance" in data["detector_results"]

def test_history_crud_flow(client):
    # 1. Create text analysis
    res = client.post("/api/v1/analyze/text", json={"text": "Meeting for lunch tomorrow."})
    analysis_id = res.json()["analysis_id"]

    # 2. Retrieve detail
    detail = client.get(f"/api/v1/analyses/{analysis_id}")
    assert detail.status_code == 200
    assert detail.json()["analysis_id"] == analysis_id

    # 3. Check list
    hist_list = client.get("/api/v1/analyses?limit=10")
    assert hist_list.status_code == 200
    assert any(item["analysis_id"] == analysis_id for item in hist_list.json())

    # 4. Delete record
    del_res = client.delete(f"/api/v1/analyses/{analysis_id}")
    assert del_res.status_code == 200

    # 5. Verify 404 after deletion
    detail_after = client.get(f"/api/v1/analyses/{analysis_id}")
    assert detail_after.status_code == 404
