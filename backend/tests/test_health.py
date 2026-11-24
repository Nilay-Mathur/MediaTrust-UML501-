def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "timestamp" in data

def test_system_status(client):
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "models_loaded" in data
    # Checkpoint files are intentionally not required in CI. The API stays
    # operational and reports each detector's availability independently.
    assert isinstance(data["models_loaded"]["image_detector"], bool)
    assert isinstance(data["models_loaded"]["text_detector"], bool)
