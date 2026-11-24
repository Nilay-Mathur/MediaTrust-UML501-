import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    APP_NAME: str = "MediaTrust"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMP_DIR: Path = BASE_DIR / "temp_uploads"
    MODELS_DIR: Path = BASE_DIR / "models" / "checkpoints"

    # Database
    DATABASE_URL: str = "sqlite:///" + (BASE_DIR / "mediatrust.db").resolve().as_posix()

    # Risk Engine Thresholds (0-100)
    RISK_THRESHOLD_LOW: int = 30
    RISK_THRESHOLD_MODERATE: int = 60
    RISK_THRESHOLD_HIGH: int = 85

    # File and Video Processing Limits
    MAX_IMAGE_FILE_SIZE_MB: int = 15
    MAX_VIDEO_FILE_SIZE_MB: int = 50
    MAX_VIDEO_DURATION_SECONDS: int = 180
    VIDEO_FRAME_SAMPLE_RATE: float = 1.0  # Sample 1 frame per second
    # Calibrated threshold for reel and video synthetic media detection
    VIDEO_AI_ALERT_THRESHOLD: float = 0.85
    VIDEO_AI_ALERTS_ENABLED: bool = True
    FACE_DEEPFAKE_ALERT_THRESHOLD: float = 0.85
    TEXT_THREAT_ALERT_THRESHOLD: float = 0.60
    MAX_VIDEO_FRAMES_TO_ANALYZE: int = 15
    MIN_VIDEO_FRAMES_FOR_AI_ALERT: int = 10

    # Model Artifact Paths
    IMAGE_MODEL_CHECKPOINT: str = str(MODELS_DIR / "efficientnet_b0_external.pt")
    TEXT_MODEL_PIPELINE: str = str(MODELS_DIR / "text_classifier_external.joblib")
    DEEPFAKE_VIDEO_MODEL_CHECKPOINT: str = str(MODELS_DIR / "resnext50_lstm_deepfake.pt")

    # Threat Intelligence (default disabled, no fake responses)
    ENABLE_EXTERNAL_THREAT_INTEL: bool = False
    VIRUSTOTAL_API_KEY: str = ""
    GOOGLE_SAFE_BROWSING_API_KEY: str = ""

    @property
    def cors_origins(self) -> List[str]:
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        # Allow any Chrome/Edge extension during local development
        origins.append("*")
        return origins

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
