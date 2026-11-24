import math
import re
from urllib.parse import urlparse, unquote
from typing import Dict, Any, List
from app.security.ssrf import validate_url_for_ssrf
from app.core.logging import logger

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".buzz", ".click", ".fit", ".rest", ".tk", ".ml", ".ga", 
    ".cf", ".gq", ".work", ".loan", ".zip", ".mov", ".country", ".stream"
}

HIGH_TARGET_BRANDS = [
    "paypal", "apple", "google", "microsoft", "netflix", "amazon", "chase", 
    "bankofamerica", "wellsfargo", "facebook", "instagram", "whatsapp", "binance", "coinbase"
]

PHISHING_KEYWORDS = [
    "login", "signin", "verify", "verification", "secure", "security", "update",
    "account", "banking", "wallet", "recover", "authenticate", "confirm", "billing"
]

def calculate_shannon_entropy(text: str) -> float:
    """Calculates Shannon entropy to detect algorithmically generated or randomized domains."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    for char in set(text):
        p_x = text.count(char) / length
        entropy += - p_x * math.log2(p_x)
    return entropy

class UrlAnalyzerService:
    def analyze_url(self, raw_url: str, enable_network_checks: bool = False, resolve_hostname: bool = True) -> Dict[str, Any]:
        """
        Conducts multi-layer lexical, cryptographic, and structural analysis of a URL.
        """
        raw_url = raw_url.strip()
        if not raw_url.startswith(("http://", "https://")):
            # Add protocol for uniform parsing if omitted
            raw_url = "http://" + raw_url

        try:
            parsed = urlparse(raw_url)
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Invalid URL syntax: {str(e)}",
                "url": raw_url,
                "findings": [],
                "risk_indicators": []
            }

        hostname = parsed.hostname or ""
        port = parsed.port
        path = parsed.path or ""
        query = parsed.query or ""
        scheme = parsed.scheme.lower()

        findings: List[Dict[str, Any]] = []
        indicators: List[str] = []
        lexical_risk_score = 0

        # Check 1: Scheme Check
        is_https = scheme == "https"
        if not is_https:
            findings.append({
                "rule": "INSECURE_PROTOCOL_HTTP",
                "severity": "moderate",
                "description": "URL uses unencrypted plaintext HTTP transport instead of HTTPS.",
                "evidence": f"Scheme is '{scheme}'"
            })
            indicators.append("Plaintext HTTP protocol")
            lexical_risk_score += 20
        else:
            findings.append({
                "rule": "HTTPS_PRESENT",
                "severity": "info",
                "description": "Connection offers TLS encryption. (Note: TLS does not indicate domain trustworthiness).",
                "evidence": "Valid HTTPS scheme detected"
            })

        # Check 2: Raw IP address as Hostname
        is_ip_host = False
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname) or ":" in hostname:
            is_ip_host = True
            findings.append({
                "rule": "NUMERIC_IP_HOST",
                "severity": "high",
                "description": "URL uses an IP address instead of a registered domain name, common in malicious host bypass.",
                "evidence": f"Hostname: {hostname}"
            })
            indicators.append("Direct IP address hostname")
            lexical_risk_score += 35

        # Check 3: Internationalized Domain (IDN) and Punycode
        is_punycode = False
        decoded_punycode = hostname
        if hostname.startswith("xn--") or ".xn--" in hostname:
            is_punycode = True
            try:
                decoded_punycode = hostname.encode("ascii").decode("idna")
            except Exception:
                decoded_punycode = hostname
            findings.append({
                "rule": "PUNYCODE_IDN_HOMOGRAPH",
                "severity": "high",
                "description": "Punycode domain detected. May utilize homograph substitution (visual spoofing of characters).",
                "evidence": f"Encoded: {hostname} -> Decoded: {decoded_punycode}"
            })
            indicators.append("Punycode homoglyph candidate")
            lexical_risk_score += 40

        # Check 4: Suspicious TLD
        tld_match = None
        for tld in SUSPICIOUS_TLDS:
            if hostname.endswith(tld):
                tld_match = tld
                break
        if tld_match:
            findings.append({
                "rule": "SUSPICIOUS_HIGH_ABUSE_TLD",
                "severity": "moderate",
                "description": f"Domain utilizes top-level domain '{tld_match}' known for high abuse/spam rates.",
                "evidence": f"TLD: {tld_match}"
            })
            indicators.append(f"High-abuse TLD ({tld_match})")
            lexical_risk_score += 25

        # Check 5: Deceptive Brand Subdomain / Target Impersonation
        hostname_parts = hostname.lower().split('.')
        for brand in HIGH_TARGET_BRANDS:
            # Check if brand appears in the hostname, but the registered root domain is NOT the brand's official domain
            if brand in hostname.lower():
                # Legitimate if root domain is e.g. paypal.com
                is_legit_brand = (
                    hostname.endswith(f".{brand}.com") or 
                    hostname == f"{brand}.com" or 
                    hostname.endswith(f".{brand}.org") or
                    hostname.endswith(f".{brand}.net")
                )
                if not is_legit_brand:
                    findings.append({
                        "rule": "DECEPTIVE_BRAND_IMPERSONATION",
                        "severity": "critical",
                        "description": f"Target brand '{brand}' appears in subdomains or path while host domain belongs to a different owner.",
                        "evidence": f"Brand token '{brand}' inside '{hostname}'"
                    })
                    indicators.append(f"Brand impersonation ({brand})")
                    lexical_risk_score += 50
                    break

        # Check 6: Phishing Keywords in Path or Hostname
        matched_keywords = []
        combined_path_host = (hostname + path + query).lower()
        for kw in PHISHING_KEYWORDS:
            if re.search(r'\b' + kw + r'\b', combined_path_host) or kw in hostname:
                matched_keywords.append(kw)
        if len(matched_keywords) >= 2:
            findings.append({
                "rule": "MULTIPLE_PHISHING_KEYWORDS",
                "severity": "high",
                "description": f"URL contains multiple credential harvesting keywords ({', '.join(matched_keywords)}).",
                "evidence": f"Found keywords: {matched_keywords}"
            })
            indicators.append(f"Harvesting terms: {', '.join(matched_keywords)}")
            lexical_risk_score += 30

        # Check 7: Subdomain Depth and Character Entropy
        subdomain_count = len(hostname_parts)
        if subdomain_count >= 5:
            findings.append({
                "rule": "EXCESSIVE_SUBDOMAIN_DEPTH",
                "severity": "moderate",
                "description": "Unusually deep subdomain hierarchy (>4 levels), often used to evade lexical filters.",
                "evidence": f"{subdomain_count} domain levels in '{hostname}'"
            })
            indicators.append("Deep subdomain nesting")
            lexical_risk_score += 20

        entropy = calculate_shannon_entropy(hostname.replace('.', ''))
        if entropy > 4.5 and len(hostname) > 15:
            findings.append({
                "rule": "HIGH_DOMAIN_ENTROPY",
                "severity": "moderate",
                "description": f"High character entropy ({entropy:.2f}), consistent with automated domain generation (DGA).",
                "evidence": f"Calculated Shannon entropy: {entropy:.2f}"
            })
            indicators.append("High entropy randomized hostname")
            lexical_risk_score += 20

        # Check 8: Non-Standard Ports
        if port and port not in (80, 443, 8080):
            findings.append({
                "rule": "NON_STANDARD_PORT",
                "severity": "moderate",
                "description": f"URL connects on unusual non-standard port {port}.",
                "evidence": f"Port: {port}"
            })
            indicators.append(f"Non-standard port ({port})")
            lexical_risk_score += 15

        # Check 9: Resolve only when the caller may use the URL for network access.
        if resolve_hostname:
            ssrf_safe, ssrf_reason, resolved_ip = validate_url_for_ssrf(raw_url)
            ssrf_status = {
                "is_safe_for_network_fetch": ssrf_safe,
                "resolved_ip": resolved_ip,
                "protection_note": "Server-Side Request Forgery protection active. Internal and metadata addresses blocked."
            }
        else:
            ssrf_safe, ssrf_reason, resolved_ip = None, None, None
            ssrf_status = {
                "is_safe_for_network_fetch": None,
                "resolved_ip": None,
                "protection_note": "Hostname was not resolved because this page scan does not fetch URLs."
            }
        if resolve_hostname and not ssrf_safe and ssrf_reason:
            findings.append({
                "rule": "SSRF_RESTRICTION_TRIGGERED",
                "severity": "critical",
                "description": f"URL attempts to reference prohibited network range or unroutable host: {ssrf_reason}",
                "evidence": f"SSRF rejection reason: {ssrf_reason}"
            })
            lexical_risk_score += 45

        # Normalize score 0 to 100
        lexical_risk_score = min(100, lexical_risk_score)

        return {
            "status": "completed",
            "url": raw_url,
            "hostname": hostname,
            "is_https": is_https,
            "is_ip_host": is_ip_host,
            "is_punycode": is_punycode,
            "decoded_punycode": decoded_punycode,
            "lexical_risk_score": lexical_risk_score,
            "indicators": indicators,
            "findings": findings,
            "ssrf_verification": ssrf_status,
            "threat_intel_status": "External intelligence queries disabled by default (no fabricated metrics).",
            "model_version": "Heuristic-Lexical-URL-v1.0"
        }

url_analyzer_service = UrlAnalyzerService()
