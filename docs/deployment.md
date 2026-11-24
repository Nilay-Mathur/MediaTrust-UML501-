# MediaTrust Deployment & Operations Guide

## 1. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js v18+ / v20+
- Git

### Step-by-Step Execution
1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd MediaTrust
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   pip install pydantic-settings
   ```

3. **Generate Fixtures & Train Models**:
   ```bash
   python scripts/generate_sample_fixtures.py
   python scripts/train_image_classifier.py
   ```

4. **Start FastAPI Backend**:
   ```bash
   python app/main.py
   # Or using uvicorn directly:
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Frontend Setup & Execution**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

6. **Load Browser Extension**:
   - Open Chrome or Edge.
   - Navigate to `chrome://extensions` or `edge://extensions`.
   - Enable "Developer mode" in the top-right toggle.
   - Click "Load unpacked" and select the `MediaTrust/extension` directory.

---

## 2. Docker & Containerized Deployment

MediaTrust provides a root `Dockerfile` and `docker-compose.yml` for unified container deployment:

```bash
docker-compose up --build -d
```

### Healthcheck
The backend container includes an automated health probe:
```bash
curl -f http://localhost:8000/api/v1/health
```

---

## 3. Production Hardening Checklist
1. **Database**: Configure a managed PostgreSQL database URL in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@db.mediatrust.internal:5432/mediatrust
   ```
2. **CORS Whitelist**: Replace wildcard origins with your production web domain:
   ```env
   ALLOWED_ORIGINS=https://mediatrust.yourdomain.edu
   ```
3. **TLS/SSL Reverse Proxy**: Terminate TLS at Nginx or Cloudflare, forwarding requests to Uvicorn via HTTP/2.
