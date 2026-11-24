# MediaTrust Threat Model & Security Architecture

This document presents a comprehensive threat model for the MediaTrust platform based on the **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

---

## 1. Threat Analysis (STRIDE Matrix)

| Threat Category | Threat Scenario | Mitigation Strategy in MediaTrust |
| :--- | :--- | :--- |
| **Spoofing** | Attacker registers a punycode domain (`xn--...`) with Cyrillic homoglyphs visually identical to target brands. | The URL analyzer decodes IDN punycode, detects character set homoglyphs, and flags mismatching brand subdomains as Critical risk. |
| **Spoofing** | Sender claims to be an executive or bank in email/SMS text. | Supervised text classifier identifies executive/authority impersonation keywords; the impersonation module cross-references claimed brand against origin domain. |
| **Tampering** | User alters a verified image file bitstream to introduce malicious payload. | Cryptographic SHA-256 integrity verification detects any 1-bit change against reference hashes. |
| **Repudiation** | Malicious actor denies uploading deceptive content. | Every analysis generates an immutable `analysis_id` with timestamp, SHA-256 digest, and evidence breakdown logged in the database. |
| **Information Disclosure** | Attacker enters `http://169.254.169.254/latest/meta-data/` to access AWS/GCP cloud credentials (SSRF). | The SSRF guard resolves hostnames before fetching, completely blocking loopback, link-local, private RFC 1918, and metadata address blocks. |
| **Information Disclosure** | Server errors reveal internal directory paths and database connection strings. | Centralized FastAPI exception handlers intercept all unhandled exceptions and return sanitized generic error messages. |
| **Denial of Service** | Attacker uploads a 4GB video file or decompression bomb. | Strict file limits enforce a 15MB limit on images, 50MB limit on videos, and a 180s duration ceiling. Processing runs with OpenCV bounded sampling. |
| **Denial of Service** | Browser extension floods background API while user rapidly scrolls through social reels. | Content script applies a 1200ms debounce timer and maintains a deduplicated cache (`Set`) of analyzed video IDs. |
| **Elevation of Privilege** | Attacker uploads executable PHP or shell script disguised as `.jpg`. | Magic byte signature verification checks initial file bytes (`\xFF\xD8\xFF` for JPEG, `\x89PNG` for PNG), rejecting renamed binaries. Uploaded files are never executed. |
| **Elevation of Privilege** | Webpage attempts to execute privileged browser extension APIs. | Extension message passing enforces strict type validation and isolates DOM injections inside an encapsulated **Shadow DOM**. |

---

## 2. Server-Side Request Forgery (SSRF) Defense

MediaTrust implements defense-in-depth against SSRF:
1. **Scheme Whitelist**: Only `http` and `https` schemes are accepted. Schemes such as `file://`, `gopher://`, `ftp://`, and `ldap://` are immediately rejected.
2. **DNS Resolution Verification**: The hostname is resolved via `socket.getaddrinfo()`.
3. **Blacklisted IP Ranges**: Any resolved IP address within the following subnets is rejected:
   - `0.0.0.0/8`
   - `10.0.0.0/8` (Private Class A)
   - `127.0.0.0/8` (Loopback)
   - `169.254.0.0/16` (Link-local & AWS/Azure/GCP metadata)
   - `172.16.0.0/12` (Private Class B)
   - `192.168.0.0/16` (Private Class C)
   - `::1/128`, `fc00::/7`, `fe80::/10` (IPv6 Loopback and Unique Local)

---

## 3. Extension Security & Privacy Boundary

- **Manifest V3 Only**: Prohibits remote script execution (`unsafe-eval` is disabled).
- **Styling & DOM Isolation**: All in-page notification widgets use `Element.attachShadow({ mode: 'open' })` to guarantee no CSS leakage or host page JavaScript script hijacking.
- **Data Minimization**: The extension extracts only visible text and accessible media URLs for the active video. It explicitly avoids inspecting input fields, passwords, authentication cookies, or private messaging inputs.
