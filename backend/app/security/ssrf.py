import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional

BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local / Cloud Metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),            # IPv6 link-local
    ipaddress.ip_network("ff00::/8"),             # IPv6 multicast
]

def is_ip_allowed(ip_str: str) -> bool:
    """Verifies that an IP address is a public, globally routable address and not private/internal."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
            return False
        for net in BLOCKED_NETWORKS:
            if ip_obj in net:
                return False
        return True
    except ValueError:
        return False

def validate_url_for_ssrf(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates a URL against SSRF vulnerabilities.
    Returns: (is_safe, error_reason, resolved_ip)
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL supplied", None

    url_clean = url.strip()
    try:
        parsed = urlparse(url_clean)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}", None

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted.", None

    hostname = parsed.hostname
    if not hostname:
        return False, "URL does not contain a valid hostname.", None

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        return False, f"Restricted internal destination: '{hostname}'. Access prohibited.", None

    # Resolve IP address safely
    try:
        resolved_ips = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not resolved_ips:
            return False, f"Unable to resolve host '{hostname}' via DNS.", None

        for item in resolved_ips:
            resolved_ip = item[4][0]
            if not is_ip_allowed(resolved_ip):
                return False, f"Host '{hostname}' resolves to restricted/internal IP {resolved_ip}.", resolved_ip

        return True, "", resolved_ips[0][4][0]
    except socket.gaierror:
        # Domain cannot be resolved - safe from SSRF but unreachable
        return False, f"Domain name '{hostname}' could not be resolved.", None
    except Exception as e:
        return False, f"Network validation error: {str(e)}", None
