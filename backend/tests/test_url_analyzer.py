from app.ml.url_analyzer.service import url_analyzer_service

def test_url_analyzer_brand_impersonation():
    res = url_analyzer_service.analyze_url("http://paypal.com.account-update.xyz/login")
    assert res["status"] == "completed"
    assert res["lexical_risk_score"] >= 50
    # Should identify brand impersonation
    rules = [f["rule"] for f in res["findings"]]
    assert "DECEPTIVE_BRAND_IMPERSONATION" in rules

def test_url_analyzer_numeric_ip():
    res = url_analyzer_service.analyze_url("http://198.51.100.25/signin")
    assert res["is_ip_host"] is True
    rules = [f["rule"] for f in res["findings"]]
    assert "NUMERIC_IP_HOST" in rules
