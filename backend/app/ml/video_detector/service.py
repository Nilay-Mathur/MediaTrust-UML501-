import os
import cv2
import tempfile
import numpy as np
from typing import Dict, Any, List
from PIL import Image
import io
from app.core.config import settings
from app.core.logging import logger
from app.ml.image_detector.service import image_detector_service

class VideoDetectorService:
    def __init__(self):
        self.max_duration_seconds = settings.MAX_VIDEO_DURATION_SECONDS
        self.max_frames_to_sample = settings.MAX_VIDEO_FRAMES_TO_ANALYZE
        self.sample_rate = settings.VIDEO_FRAME_SAMPLE_RATE

    def analyze_video(self, video_bytes: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Extracts frames at bounded sampling rate, runs image detector inference on each frame,
        and aggregates into a structured temporal report.
        """
        temp_video_path = None
        try:
            # Save video bytes to temporary file for OpenCV decoding
            suffix = os.path.splitext(original_filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.TEMP_DIR) as f:
                f.write(video_bytes)
                temp_video_path = f.name

            cap = cv2.VideoCapture(temp_video_path)
            if not cap.isOpened():
                return {
                    "status": "failed",
                    "error": "Unsupported video codec or corrupted video container.",
                    "video_level_summary": "Processing failed: OpenCV could not decode the video file.",
                    "frames_analyzed": 0,
                    "frame_timeline": [],
                    "aggregate_ai_score": 0.0
                }

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if fps <= 0 or total_frames <= 0:
                cap.release()
                return {
                    "status": "failed",
                    "error": "Invalid video stream metadata (FPS or frame count is zero).",
                    "frames_analyzed": 0,
                    "frame_timeline": [],
                    "aggregate_ai_score": 0.0
                }

            duration_sec = total_frames / fps
            if duration_sec > self.max_duration_seconds:
                cap.release()
                return {
                    "status": "failed",
                    "error": f"Video duration ({round(duration_sec, 1)}s) exceeds maximum permitted limit of {self.max_duration_seconds}s.",
                    "frames_analyzed": 0,
                    "frame_timeline": [],
                    "aggregate_ai_score": 0.0
                }

            # Calculate frame sampling step
            step = max(1, int(fps * self.sample_rate))
            frame_timeline = []
            frame_indices_to_sample = list(range(0, total_frames, step))[:self.max_frames_to_sample]

            logger.info(f"Analyzing video '{original_filename}': duration={duration_sec:.1f}s, fps={fps:.1f}, sampling {len(frame_indices_to_sample)} frames")

            for frame_idx in frame_indices_to_sample:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue

                timestamp_sec = round(frame_idx / fps, 2)
                # Convert BGR (OpenCV) to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(rgb_frame)

                # Convert to JPEG bytes for detector
                buf = io.BytesIO()
                pil_frame.save(buf, format="JPEG", quality=80)
                frame_bytes = buf.getvalue()

                # Infer using image detector
                inference_res = image_detector_service.predict(frame_bytes)

                frame_timeline.append({
                    "frame_index": frame_idx,
                    "timestamp_sec": timestamp_sec,
                    "ai_generated_score": inference_res.get("ai_generated_score", 0.0),
                    "real_score": inference_res.get("real_score", 0.0),
                    "prediction": inference_res.get("prediction", "unknown"),
                    "confidence": inference_res.get("confidence", 0.0)
                })

            cap.release()

            if not frame_timeline:
                return {
                    "status": "inconclusive",
                    "error": "No frames could be successfully sampled from video.",
                    "frames_analyzed": 0,
                    "frame_timeline": [],
                    "aggregate_ai_score": 0.0
                }

            if len(frame_timeline) < settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT:
                return {
                    "status": "inconclusive",
                    "error": f"Need at least {settings.MIN_VIDEO_FRAMES_FOR_AI_ALERT} sampled frames for a video AI verdict; received {len(frame_timeline)}.",
                    "frames_analyzed": len(frame_timeline),
                    "frame_timeline": frame_timeline,
                    "ai_decision_threshold": settings.VIDEO_AI_ALERT_THRESHOLD,
                    "ai_alert_enabled": settings.VIDEO_AI_ALERTS_ENABLED,
                    "model_version": "EfficientNet-B0-VideoSampler-v1.0",
                }

            # Conservative Aggregation Strategy:
            # We compute the 85th percentile peak anomaly score and the average score.
            # Deepfake artifacts can appear in specific keyframes rather than uniformly throughout.
            scores = [f["ai_generated_score"] for f in frame_timeline]
            peak_85th = float(np.percentile(scores, 85))
            mean_score = float(np.mean(scores))
            max_score = float(np.max(scores))

            # Conservative combination: 60% weight to peak, 40% weight to mean
            aggregate_score = round(0.60 * peak_85th + 0.40 * mean_score, 4)

            summary_text = (
                f"Evaluated {len(frame_timeline)} frames across {duration_sec:.1f} seconds. "
                f"Peak frame synthetic score reached {max_score:.2f}, with an 85th percentile of {peak_85th:.2f} "
                f"and mean frame score of {mean_score:.2f}."
            )

            return {
                "status": "completed",
                "duration_seconds": round(duration_sec, 2),
                "resolution": f"{width}x{height}",
                "fps": round(fps, 2),
                "frames_analyzed": len(frame_timeline),
                "frame_timeline": frame_timeline,
                "aggregate_ai_score": aggregate_score,
                "ai_decision_threshold": settings.VIDEO_AI_ALERT_THRESHOLD,
                "ai_alert_enabled": settings.VIDEO_AI_ALERTS_ENABLED,
                "peak_frame_score": round(max_score, 4),
                "mean_frame_score": round(mean_score, 4),
                "aggregation_methodology": "Conservative pooling: 60% 85th percentile anomaly peak + 40% sequence mean",
                "summary": summary_text,
                "model_version": "EfficientNet-B0-VideoSampler-v1.0",
                "limitations": [
                    "Analysis samples frames independently; temporal consistency and motion-blur deepfake artifacts are not modeled with 3D-CNN or optical flow.",
                    "Compression artifacts from platform transcoding (e.g. Reels, Shorts) can induce noise on static frame detectors.",
                    "Face manipulation is evaluated purely via general generative texture analysis, not facial landmark tracking."
                ]
            }
        except Exception as e:
            logger.error(f"Video analysis error: {str(e)}")
            return {
                "status": "failed",
                "error": f"Video analysis error: {str(e)}",
                "frames_analyzed": 0,
                "frame_timeline": [],
                "aggregate_ai_score": 0.0
            }
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception:
                    pass

video_detector_service = VideoDetectorService()
