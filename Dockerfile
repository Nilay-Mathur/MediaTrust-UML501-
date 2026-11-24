# Production Dockerfile for MediaTrust Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including OpenCV dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and model configurations
COPY backend /app/backend
COPY models /app/models
COPY datasets/sample_data /app/datasets/sample_data

ENV PYTHONPATH=/app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
