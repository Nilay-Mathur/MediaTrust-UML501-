"""ResNeXt50 + LSTM inference for face-manipulated video clips.

Architecture and preprocessing are adapted from the user-provided
AI-Generated-Photo-Video-Detector repository. Its checkpoint is loaded using
weights_only=True; no serialized Python objects are accepted.
"""
from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List, Optional, Sequence

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

from app.core.config import settings
from app.core.logging import logger


class ResNeXtLSTM(nn.Module):
    """State-dict-compatible architecture from the upstream training notebook."""
    def __init__(self) -> None:
        super().__init__()
        backbone = models.resnext50_32x4d(weights=None)
        self.model = nn.Sequential(*list(backbone.children())[:-2])
        self.lstm = nn.LSTM(input_size=2048, hidden_size=2048, num_layers=1, bidirectional=False, bias=False)
        self.relu = nn.LeakyReLU()
        self.dp = nn.Dropout(0.4)
        self.linear1 = nn.Linear(2048, 2)
        self.avgpool = nn.AdaptiveAvgPool2d(1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, sequence, channels, height, width = x.shape
        fmap = self.model(x.reshape(batch * sequence, channels, height, width))
        pooled = self.avgpool(fmap).reshape(batch, sequence, 2048)
        temporal, _ = self.lstm(pooled, None)
        # The upstream training notebook averages temporal outputs before its head.
        return self.dp(self.linear1(temporal.mean(dim=1)))


class DeepfakeVideoDetectorService:
    SEQUENCE_LENGTH = 20
    INPUT_SIZE = 112
    MODEL_VERSION = "ResNeXt50-LSTM-External-v1"

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: ResNeXtLSTM | None = None
        self.model_loaded = False
        self.checkpoint_path = settings.DEEPFAKE_VIDEO_MODEL_CHECKPOINT
        self.transform = transforms.Compose([
            transforms.Resize((self.INPUT_SIZE, self.INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            cascade = cv2.CascadeClassifier(cascade_path)
            if not cascade.empty():
                self.face_cascade = cascade
        except Exception:
            pass
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self.checkpoint_path):
            logger.warning("ResNeXt-LSTM video checkpoint not found: %s", self.checkpoint_path)
            return
        try:
            model = ResNeXtLSTM().to(self.device)
            weights = torch.load(self.checkpoint_path, map_location=self.device, weights_only=True)
            if isinstance(weights, dict) and "state_dict" in weights:
                weights = weights["state_dict"]
            if not isinstance(weights, dict):
                raise ValueError("Expected a tensor state dictionary.")
            model.load_state_dict(weights, strict=True)
            model.eval()
            self.model = model
            self.model_loaded = True
            logger.info("Loaded ResNeXt50-LSTM deepfake checkpoint on %s", self.device)
        except Exception as exc:
            self.model = None
            self.model_loaded = False
            logger.exception("Could not load ResNeXt50-LSTM checkpoint: %s", exc)

    def _face_crop(self, rgb: np.ndarray) -> Optional[np.ndarray]:
        """Return a detected face crop; never feed a whole non-face frame to this model."""
        if self.face_cascade is None:
            return None
        try:
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
            if len(faces) == 0:
                return None
            x, y, width, height = max(faces, key=lambda box: box[2] * box[3])
            pad_x, pad_y = int(width * 0.12), int(height * 0.12)
            x0, y0 = max(0, x - pad_x), max(0, y - pad_y)
            x1, y1 = min(rgb.shape[1], x + width + pad_x), min(rgb.shape[0], y + height + pad_y)
            return rgb[y0:y1, x0:x1] if x1 > x0 and y1 > y0 else None
        except Exception:
            return None

    def predict_frames(self, frames_rgb: Sequence[np.ndarray]) -> Dict[str, Any]:
        if not self.model_loaded or self.model is None:
            return {"status": "unavailable", "error": "The ResNeXt-LSTM checkpoint is not loaded.", "model_version": self.MODEL_VERSION}
        if not frames_rgb or len(frames_rgb) == 0:
            return {
                "status": "inconclusive",
                "error": "No video frames available for temporal deepfake analysis.",
                "frames_analyzed": 0,
                "model_version": self.MODEL_VERSION,
            }
        indices = np.linspace(0, len(frames_rgb) - 1, self.SEQUENCE_LENGTH, dtype=np.int64)
        try:
            face_crops: List[Optional[np.ndarray]] = []
            for index in indices:
                frame = np.asarray(frames_rgb[int(index)])
                if frame.ndim != 3 or frame.shape[2] < 3:
                    face_crops.append(None)
                    continue
                frame = frame[:, :, :3].astype(np.uint8, copy=False)
                face_crops.append(self._face_crop(frame))

            detected_indices = [i for i, crop in enumerate(face_crops) if crop is not None]
            min_face_frames = 1 if len(frames_rgb) <= 3 else max(2, self.SEQUENCE_LENGTH // 4)
            if len(detected_indices) < min_face_frames:
                return {
                    "status": "inconclusive",
                    "error": f"No consistent face detected across sampled frames ({len(detected_indices)} face frames detected). Evaluated via general generative texture analysis.",
                    "frames_analyzed": len(frames_rgb),
                    "face_frames_detected": len(detected_indices),
                    "face_crops_applied": False,
                    "model_version": self.MODEL_VERSION,
                }

            # Fill detector misses from the nearest detected face frame
            for i, crop in enumerate(face_crops):
                if crop is None:
                    nearest = min(detected_indices, key=lambda j: abs(j - i))
                    face_crops[i] = face_crops[nearest]
            tensors = [self.transform(Image.fromarray(crop, mode="RGB")) for crop in face_crops if crop is not None]
            if len(tensors) != self.SEQUENCE_LENGTH:
                raise ValueError(f"Could only prepare {len(tensors)} of {self.SEQUENCE_LENGTH} face frames.")
            batch = torch.stack(tensors).unsqueeze(0).to(self.device)
            with torch.inference_mode():
                logits = self.model(batch)
                # Upstream labels: 0=FAKE, 1=REAL.
                probabilities = F.softmax(logits, dim=1)[0].detach().cpu().numpy()
            fake_score, real_score = float(probabilities[0]), float(probabilities[1])
            return {
                "status": "completed",
                "fake_probability": round(fake_score, 4),
                "real_probability": round(real_score, 4),
                "prediction": "possible_deepfake" if fake_score >= 0.5 else "no_strong_deepfake_signal",
                "decision_threshold": settings.FACE_DEEPFAKE_ALERT_THRESHOLD,
                "frames_analyzed": len(frames_rgb),
                "face_crops_applied": True,
                "face_frames_detected": len(detected_indices),
                "model_version": self.MODEL_VERSION,
                "limitations": [
                    "This model targets face-manipulated/deepfake videos and is not a general detector for fully AI-generated scenes, animals, or animation.",
                    "The upstream checkpoint reports training/evaluation on face-deepfake datasets, but this archive did not include a reproducible evaluation report or calibrated threshold.",
                    "A high score is an unverified model signal, not proof of manipulation; social-platform transcoding may reduce accuracy.",
                ],
            }
        except Exception as exc:
            logger.exception("ResNeXt-LSTM video inference failed: %s", exc)
            return {"status": "failed", "error": "Deepfake frame-sequence inference failed.", "model_version": self.MODEL_VERSION}

    def predict_video_bytes(self, video_bytes: bytes, filename: str) -> Dict[str, Any]:
        if not self.model_loaded or self.model is None:
            return {"status": "unavailable", "error": "The ResNeXt-LSTM checkpoint is not loaded.", "model_version": self.MODEL_VERSION}
        temp_path = None
        try:
            suffix = os.path.splitext(filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.TEMP_DIR) as stream:
                stream.write(video_bytes)
                temp_path = stream.name
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                return {"status": "inconclusive", "error": "Could not decode this video for temporal deepfake analysis.", "model_version": self.MODEL_VERSION}
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if total < self.SEQUENCE_LENGTH or fps <= 0:
                cap.release()
                return {"status": "inconclusive", "error": f"Video needs at least {self.SEQUENCE_LENGTH} decodable frames for temporal deepfake analysis.", "frames_analyzed": 0, "model_version": self.MODEL_VERSION}
            # Match the upstream short sequential clip convention: sample across the
            # opening two seconds (or the whole shorter clip) without altering playback.
            end_index = min(total - 1, max(self.SEQUENCE_LENGTH - 1, round(2.0 * fps)))
            indices = np.linspace(0, end_index, self.SEQUENCE_LENGTH, dtype=np.int64)
            frames = []
            for index in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(index))
                ok, frame = cap.read()
                if ok and frame is not None:
                    frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            cap.release()
            result = self.predict_frames(frames)
            result["sampling_window_seconds"] = round(end_index / fps, 2) if fps > 0 else None
            return result
        except Exception as exc:
            logger.exception("Could not prepare uploaded video for deepfake model: %s", exc)
            return {"status": "failed", "error": "Could not prepare this video for deepfake analysis.", "model_version": self.MODEL_VERSION}
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


deepfake_video_detector_service = DeepfakeVideoDetectorService()
