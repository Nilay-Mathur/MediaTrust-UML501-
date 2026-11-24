# MediaTrust API Reference (v1)

Base URL: `http://127.0.0.1:8000/api/v1`

---

### System Endpoints
- `GET /health`: Health probe returning operational status.
- `GET /system/status`: Returns platform status, loaded ML models, and runtime details.

---

### Analysis Endpoints
- `POST /analyze/image`: Multipart form upload (`file`, optional `claimed_hash`). Returns `AnalysisResponse`.
- `POST /analyze/video`: Multipart form upload (`file`). Extracts keyframes and returns `AnalysisResponse`.
- `POST /analyze/text`: JSON body (`text`, optional `claimed_sender`, optional `context_url`).
- `POST /analyze/url`: JSON body (`url`, optional `enable_network_checks`).
- `POST /analyze/impersonation`: JSON body (`claimed_entity`, optional `domain`, optional `message_text`).
- `POST /analyze/page`: JSON body (`url`, `page_title`, `text_content`, `links`, `video_urls`). Used by Chrome extension.

---

### History & Analytics Endpoints
- `GET /analyses`: Paginated list of past analyses (`input_type`, `risk`, `limit`, `offset`).
- `GET /analyses/{analysis_id}`: Retrieves full analysis audit record by ID.
- `DELETE /analyses/{analysis_id}`: Deletes record permanently for privacy compliance.
- `GET /analytics/summary`: Aggregate counts by risk tier and input type.

---

### Model Registry & Metrics
- `GET /models`: Returns active model architectures and explainability mechanisms.
- `GET /models/{model_name}/metrics`: Returns accuracy, precision, recall, F1, ROC-AUC, and confusion matrix.

---

### Integrity Endpoints
- `POST /integrity/hash`: Computes SHA-256 on uploaded file.
- `POST /integrity/verify`: Verifies file hash against claimed reference.
