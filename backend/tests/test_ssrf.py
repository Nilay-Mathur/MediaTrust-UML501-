from app.security.ssrf import validate_url_for_ssrf, is_ip_allowed

def test_internal_ips_blocked():
    assert is_ip_allowed("127.0.0.1") is False
    assert is_ip_allowed("10.0.1.5") is False
    assert is_ip_allowed("192.168.1.1") is False
    assert is_ip_allowed("169.254.169.254") is False
    assert is_ip_allowed("::1") is False

def test_public_ips_allowed():
    assert is_ip_allowed("8.8.8.8") is True
    assert is_ip_allowed("1.1.1.1") is True

def test_ssrf_url_validation():
    is_safe, reason, _ = validate_url_for_ssrf("http://127.0.0.1:8080/admin")
    assert is_safe is False
    assert "Restricted internal destination" in reason

    is_safe, reason, _ = validate_url_for_ssrf("http://localhost:3000")
    assert is_safe is False

    is_safe, reason, _ = validate_url_for_ssrf("file:///etc/passwd")
    assert is_safe is False
    assert "Unsupported URL scheme" in reason
