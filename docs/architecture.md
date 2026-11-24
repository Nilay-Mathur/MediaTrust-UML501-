# MediaTrust: Software Architecture & Engineering Design Document

This document provides complete Software Engineering diagrams and technical specifications for the MediaTrust platform, prepared in accordance with third-year B.Tech Computer Science and Engineering capstone project standards.

---

## 1. System Context & Architecture Overview

MediaTrust follows a decoupled, three-tier micro-service architecture:
1. **Client Tier**: Web Client (React 18 + Vite + Tailwind CSS) and Chromium Browser Extension (Manifest V3).
2. **Application & Security Tier**: FastAPI asynchronous application gateway, SSRF validation filter, request sanitizer, and SQLAlchemy ORM.
3. **Machine Learning & Risk Intelligence Tier**: PyTorch transfer learning inference (EfficientNet-B0), Scikit-Learn TF-IDF pipeline, OpenCV temporal frame sampler, and the Centralized Risk Engine.

```mermaid
flowchart TB
    subgraph ClientLayer["Client Layer"]
        Web["Web Application (React + Vite)"]
        ExtPopup["Browser Extension Popup"]
        ExtFeed["Social Reel Observer (Content Script)"]
    end

    subgraph APILayer["API Gateway & Security Layer"]
        FastAPI["FastAPI REST Server (:8000)"]
        SSRF["SSRF Guard & IP Validator"]
        Sanitizer["MIME & Magic Byte File Sanitizer"]
    end

    subgraph MLLayer["Machine Learning & Intelligence Subsystems"]
        ImgModel["EfficientNet-B0 AI Image Detector"]
        GradCAM["Grad-CAM Interpretability Engine"]
        TxtModel["TF-IDF + Logistic Regression Text Classifier"]
        VidSampler["OpenCV Temporal Video Sampler"]
        URLEngine["Heuristic Lexical URL Analyzer"]
        ProvEngine["SHA-256 & EXIF Provenance Engine"]
    end

    subgraph CoreEngine["Centralized Policy Engine"]
        RiskEngine["Centralized Risk Aggregator"]
        EvidenceGen["Evidence Normalization & Calibration"]
    end

    subgraph DataLayer["Persistence Layer"]
        DB[("SQLAlchemy Database (SQLite / Postgres)")]
        AuditLog["Audit & Integrity History"]
    end

    Web -->|HTTP REST| FastAPI
    ExtPopup -->|HTTP REST| FastAPI
    ExtFeed -->|HTTP REST| FastAPI

    FastAPI --> SSRF
    FastAPI --> Sanitizer

    Sanitizer --> ImgModel
    Sanitizer --> VidSampler
    SSRF --> URLEngine
    FastAPI --> TxtModel
    FastAPI --> ProvEngine

    ImgModel --> GradCAM
    ImgModel --> EvidenceGen
    VidSampler --> ImgModel
    TxtModel --> EvidenceGen
    URLEngine --> EvidenceGen
    ProvEngine --> EvidenceGen

    EvidenceGen --> RiskEngine
    RiskEngine --> DB
    RiskEngine --> AuditLog
    RiskEngine --> FastAPI
```

---

## 2. Data Flow Diagrams (DFD)

### Level 0 DFD (Context Diagram)

```mermaid
flowchart LR
    User["End User / Browser Extension"]
    System["MediaTrust Digital Trust Engine"]
    DB[("Analysis Audit Database")]

    User -->|"Uploads Media / Submits URL / Feeds Social Video"| System
    System -->|"Returns Risk Score, Grad-CAM, Evidence & Recommendations"| User
    System <-->|"Stores & Retrieves Historical Analyses"| DB
```

### Level 1 DFD (Subsystem Data Flow)

```mermaid
flowchart TD
    In["User Input (Media, Text, URL)"] --> P1["1.0 Request Validation & SSRF Guard"]
    P1 -->|"Valid Image / Video"| P2["2.0 Computer Vision Pipeline"]
    P1 -->|"Valid Text Snippet"| P3["3.0 Supervised NLP Classifier"]
    P1 -->|"Valid URL String"| P4["4.0 Lexical Domain Analyzer"]
    P1 -->|"Binary Bitstream"| P5["5.0 SHA-256 Provenance Verifier"]

    P2 -->|"AI Likelihood & Grad-CAM"| P6["6.0 Centralized Risk Engine"]
    P3 -->|"Intent Probabilities & Top Tokens"| P6
    P4 -->|"Rule Violations & Homoglyphs"| P6
    P5 -->|"Integrity Matches & EXIF Software"| P6

    P6 --> P7["7.0 Score Aggregation & Policy Evaluation"]
    P7 --> Out["Structured Analysis Response"]
    P7 --> DB[("Analyses Store")]
```

### Level 2 DFD (Detailed Analysis Pipeline)

```mermaid
flowchart TD
    subgraph InputValidation["Step 1: Ingestion & Security Checks"]
        Raw["Raw Upload"] --> MIME["Inspect Magic Header Bytes"]
        MIME --> Size["Verify File Size & Limits"]
        Size --> SHA["Compute Cryptographic SHA-256 Digest"]
    end

    subgraph DetectorExecution["Step 2: Detector Services Execution"]
        SHA -->|"Video File"| Extract["OpenCV Bounded Keyframe Sampler (1 fps)"]
        Extract --> FrameInference["EfficientNet-B0 Frame-by-Frame Evaluation"]
        FrameInference --> Pool["Conservative Pooling (60% Peak + 40% Mean)"]

        SHA -->|"Single Image"| EfficientNet["EfficientNet-B0 Tensor Forward Pass"]
        EfficientNet --> CAM["Grad-CAM Backward Gradient Hook"]

        Raw -->|"Text / Message"| TFIDF["TF-IDF Vectorizer (1-2 ngrams)"]
        TFIDF --> LogReg["Multinomial Logistic Regression Head"]
        LogReg --> Coef["Feature Importance Dot Product Calculation"]

        Raw -->|"URL / Domain"| Puny["Punycode & Homoglyph Decoder"]
        Puny --> Subdomain["Deceptive Brand Subdomain Detection"]
        Subdomain --> SSRFCheck["DNS Resolution & Private IP Guard"]
    end

    subgraph RiskAggregation["Step 3: Centralized Risk Synthesis"]
        Pool --> Norm["Evidence Normalization"]
        CAM --> Norm
        Coef --> Norm
        SSRFCheck --> Norm
        Norm --> HeuristicScore["Calculate Policy Risk Score (0-100)"]
        HeuristicScore --> TierCategorization["Assign Tier: Low, Moderate, High, Critical"]
    end

    subgraph OutputPersist["Step 4: Audit & Delivery"]
        TierCategorization --> RecordStore["Persist Analysis Record in SQLite"]
        TierCategorization --> ClientJSON["Transmit AnalysisResponse to Client"]
    end
```

---

## 3. UML Class Diagram

```mermaid
classDiagram
    class AnalysisRecord {
        +String id
        +String input_type
        +String status
        +String overall_risk
        +int risk_score
        +String score_type
        +float confidence
        +String summary
        +String content_hash
        +String source_reference
        +List findings
        +Dict detector_results
        +List limitations
        +List recommended_actions
        +DateTime created_at
    }

    class ImageDetectorService {
        +device: torch.device
        +model: EfficientNetDeepfakeDetector
        +grad_cam: GradCAM
        +predict(image_bytes: bytes) Dict
    }

    class TextDetectorService {
        +pipeline: Pipeline
        +predict(text: str) Dict
        +_explain_prediction(text, class, vec, clf) List
    }

    class VideoDetectorService {
        +max_duration_seconds: int
        +max_frames_to_sample: int
        +sample_rate: float
        +analyze_video(video_bytes, filename) Dict
    }

    class UrlAnalyzerService {
        +analyze_url(raw_url, enable_network) Dict
        +calculate_shannon_entropy(text) float
    }

    class ProvenanceService {
        +compute_sha256(file_bytes) str
        +verify_hash(file_bytes, claimed_hash) Dict
        +inspect_image_provenance(image_bytes) Dict
    }

    class CentralizedRiskEngine {
        +threshold_low: int
        +threshold_mod: int
        +threshold_high: int
        +evaluate(input_type, detector_results, content_hash) AnalysisResponse
    }

    CentralizedRiskEngine ..> ImageDetectorService : aggregates
    CentralizedRiskEngine ..> TextDetectorService : aggregates
    CentralizedRiskEngine ..> VideoDetectorService : aggregates
    CentralizedRiskEngine ..> UrlAnalyzerService : aggregates
    CentralizedRiskEngine ..> ProvenanceService : aggregates
    CentralizedRiskEngine --> AnalysisRecord : generates
```

---

## 4. Sequence Diagrams

### Web Application Analysis Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React Web App
    participant API as FastAPI Backend
    participant Security as Security & File Validator
    participant ML as ML Detector Pipelines
    participant Engine as Centralized Risk Engine
    participant DB as SQLite / Postgres DB

    User->>Frontend: Selects Image and clicks "Analyze Content"
    Frontend->>API: POST /api/v1/analyze/image (multipart/form-data)
    API->>Security: Validate MIME bytes & check file size (<15MB)
    Security-->>API: Validated (image/jpeg)
    API->>ML: Run EfficientNet-B0 inference & Grad-CAM hook
    ML-->>API: Return AI Score (0.88), Grad-CAM JPEG Base64
    API->>Engine: Evaluate findings against Risk Policy
    Engine-->>API: Overall Risk: High, Risk Score: 82/100
    API->>DB: Persist AnalysisRecord
    API-->>Frontend: Return AnalysisResponse JSON
    Frontend->>User: Render interactive Grad-CAM viewer & Evidence Table
```

### Browser Extension Automatic Social Reel Monitoring Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant DOM as Instagram / YouTube Page
    participant Observer as Content Script (IntersectionObserver)
    participant Worker as Background Service Worker
    participant API as MediaTrust Backend API

    User->>DOM: Scrolls through Social Video Feed
    DOM->>Observer: Video element enters viewport (threshold >= 0.55)
    Observer->>Observer: Debounce timer waits 1200ms
    Observer->>Worker: Sends ANALYZE_VIDEO_FEED (Text, Links, Video URL)
    Worker->>API: POST /api/v1/analyze/page
    API->>API: Run NLP classifier & Lexical URL checks
    API-->>Worker: Return AnalysisResponse (e.g. Risk Score: 80/100 High Risk)
    Worker-->>Observer: Deliver result
    Observer->>DOM: Inject Shadow DOM notification in bottom-right corner
    User->>Observer: Clicks "Open Full Report"
    Observer->>Frontend: Opens http://localhost:5173/analysis/mt-xxxx in new tab
```

---

## 5. State Machine Diagram: Analysis Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Submitted: User submits input payload
    Submitted --> Validating: Magic bytes, size, and SSRF validation
    Validating --> Rejected: Validation failed (Malformed / SSRF Block)
    Validating --> Processing: Passed security checks

    state Processing {
        [*] --> Ingesting
        Ingesting --> ModelInference: PyTorch / Scikit-Learn Forward Pass
        ModelInference --> ExplainabilityComputation: Grad-CAM / Feature Coefficients
        ExplainabilityComputation --> [*]
    }

    Processing --> Synthesizing: Normalize findings in Risk Engine
    Synthesizing --> Evaluated: Policy risk score computed (0-100)
    Evaluated --> Persisted: Saved to SQLAlchemy DB
    Persisted --> Completed: Transmitted to client
    Completed --> [*]
    Rejected --> [*]
```

---

## 6. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    ANALYSES {
        string id PK "Unique Analysis Identifier (e.g. mt-c9a81f3b20)"
        string input_type "image | video | text | url | impersonation | page"
        string status "completed | failed | inconclusive"
        string overall_risk "low | moderate | high | critical"
        int risk_score "0 to 100 Heuristic Risk Score"
        string score_type "heuristic_risk_score"
        float confidence "Nullable Model Confidence"
        text summary "Human-readable summary text"
        string content_hash "Cryptographic SHA-256 Digest"
        string source_reference "Original filename, URL, or snippet"
        text findings "JSON Array of EvidenceItem records"
        text detector_results "JSON Object of individual detector outputs"
        text limitations "JSON Array of documented limitations"
        text recommended_actions "JSON Array of security guidance steps"
        text model_versions "JSON Object of active model versions"
        datetime created_at "UTC Timestamp"
    }
```
