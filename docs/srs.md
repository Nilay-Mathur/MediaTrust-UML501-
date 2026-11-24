# Software Requirements Specification (SRS)
## Project Name: MediaTrust — Real-Time Digital Trust and Safety Layer

### 1. Introduction
#### 1.1 Purpose
This document specifies the software requirements for **MediaTrust**, a real-time digital trust, deepfake detection, scam detection, and impersonation analysis platform designed as an integrated undergraduate capstone project in Software Engineering and Machine Learning.

#### 1.2 Scope
MediaTrust provides multi-modal threat analysis across synthetic images, social videos/reels, scam/phishing text, deceptive URLs, and identity impersonation claims, delivered through a modern Web application and a Chromium Manifest V3 browser extension.

---

### 2. Overall Description
#### 2.1 Product Perspective
MediaTrust operates as an autonomous, self-contained digital defense layer. It does not replace human judgment with opaque claims; instead, it synthesizes empirical statistical evidence with forensic checks.

#### 2.2 User Characteristics
- **General Web Users**: Individuals browsing social networks seeking automated protection from deceptive reels, investment scams, and phishing messages.
- **Cybersecurity Investigators / Students**: Analysts examining digital media for synthetic artifacts, EXIF tampering, and lexical URL homographs.

---

### 3. Functional Requirements (FR)

| Req ID | Title | Description |
| :--- | :--- | :--- |
| **FR-01** | AI Image Detection | The system shall ingest JPEG/PNG/WebP images up to 15MB, execute an EfficientNet-B0 transfer learning model, and return predicted class (`real_image` vs `ai_generated`) and calibrated confidence. |
| **FR-02** | Visual Explainability | The system shall compute Grad-CAM activation heatmaps highlighting pixel regions that influenced the image classifier's synthetic prediction. |
| **FR-03** | Video Anomaly Sampling | The system shall ingest MP4/WebM videos up to 50MB and 180s, extract keyframes at 1.0 fps via OpenCV, infer each frame, and calculate a conservative 60% peak + 40% mean anomaly score. |
| **FR-04** | Text Threat Classification | The system shall classify text messages using a supervised TF-IDF + Logistic Regression pipeline into `benign`, `scam_fraud`, `phishing_credential_theft`, or `impersonation`. |
| **FR-05** | Token Feature Importance | The system shall compute and return top contributing n-gram tokens for the predicted text category. |
| **FR-06** | Lexical URL Inspection | The system shall evaluate target URLs for punycode homographs, deceptive brand subdomains, IP hosts, non-standard ports, and high-abuse TLDs. |
| **FR-07** | SSRF Defense | The system shall resolve domain hostnames and prohibit connections to private, loopback, link-local, and cloud metadata IP ranges (`127.0.0.0/8`, `10.0.0.0/8`, `169.254.169.254`, etc.). |
| **FR-08** | Provenance & Hash Verification | The system shall calculate SHA-256 digests and inspect EXIF metadata for generative software tags (e.g. Midjourney, Stable Diffusion). |
| **FR-09** | Impersonation Analysis | The system shall check claimed organizations against origin domains and credential solicitation patterns. |
| **FR-10** | Centralized Risk Policy | The system shall synthesize findings into an honest 0–100 heuristic risk score categorized as Low, Moderate, High, or Critical. |
| **FR-11** | Audit History & Privacy | The system shall persist analysis records in a database, provide filterable audit history, and permit single-click permanent deletion. |
| **FR-12** | Automatic Social Reel Observer | The Manifest V3 extension shall use `IntersectionObserver` to detect active playing videos in social feeds, background-sample content, and inject an isolated Shadow DOM warning alert. |

---

### 4. Non-Functional Requirements (NFR)

- **NFR-01 Performance**: Image inference shall complete within < 1.5 seconds on standard x86 CPU hardware. Text classification shall complete in < 50 milliseconds.
- **NFR-02 Security**: Uploaded files shall never be executed. Path traversal characters (`../`) shall be sanitized. Unhandled exceptions shall never leak stack traces or server paths.
- **NFR-03 Reliability**: The centralized risk engine must handle missing or failed detector services gracefully without artificially increasing the risk score.
- **NFR-04 Privacy & Data Minimization**: Video frames and uploaded media shall be cleared from temporary storage immediately following inference.
- **NFR-05 Usability**: The user interface shall adhere to WCAG 2.1 AA accessibility guidelines, with dark charcoal text on clean light neutral backgrounds and clear focus states.
