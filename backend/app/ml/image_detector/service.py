import os
import io
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from typing import Dict, Any, Tuple, List
from app.core.config import settings
from app.core.logging import logger
from app.ml.image_detector.model import EfficientNetDeepfakeDetector, GradCAM, CLASS_NAMES

class ImageDetectorService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.grad_cam = None
        self.model_loaded = False
        self.ai_threshold = 0.70
        self.checkpoint_path = settings.IMAGE_MODEL_CHECKPOINT
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self._initialize_model()

    def _initialize_model(self):
        try:
            logger.info(f"Initializing EfficientNet-B0 image detector on device: {self.device}")
            if not os.path.exists(self.checkpoint_path):
                logger.warning("No trained image-detector checkpoint configured; image analysis is unavailable until one is trained.")
                self.model = None
                self.model_loaded = False
                return

            logger.info(f"Loading image detector checkpoint: {self.checkpoint_path}")
            self.model = EfficientNetDeepfakeDetector(num_classes=2, pretrained=False).to(self.device)
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device, weights_only=True)
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["state_dict"])
                self.ai_threshold = float(checkpoint.get("ai_threshold", 0.70))
            elif isinstance(checkpoint, dict):
                self.model.load_state_dict(checkpoint)
            else:
                raise ValueError("Unsupported image checkpoint format.")
            self.model_loaded = True
            self.model.eval()
            self.grad_cam = GradCAM(self.model)
        except Exception as e:
            logger.error(f"Failed to initialize image detector model: {str(e)}")
            self.model = None
            self.model_loaded = False

    def predict_ai_scores(self, image_bytes_list: List[bytes]) -> Dict[str, Any]:
        """Return per-frame AI scores without Grad-CAM, for bounded video batches."""
        if not self.model_loaded or self.model is None:
            return {"status": "unavailable", "error": "Image classification model is not loaded.", "scores": []}
        try:
            tensors = []
            for image_bytes in image_bytes_list:
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                tensors.append(self.transform(image))
            if not tensors:
                return {"status": "inconclusive", "scores": []}
            scores = []
            with torch.inference_mode():
                for offset in range(0, len(tensors), 4):
                    batch = torch.stack(tensors[offset:offset + 4]).to(self.device)
                    probabilities = F.softmax(self.model(batch), dim=1)[:, 1].detach().cpu().tolist()
                    scores.extend(float(score) for score in probabilities)
            return {"status": "completed", "scores": [round(score, 4) for score in scores]}
        except Exception as exc:
            logger.exception("Batched image inference error: %s", exc)
            return {"status": "failed", "error": "Could not classify the sampled video frames.", "scores": []}

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Executes inference on an input image.
        Returns prediction details, calibrated confidence scores, and Grad-CAM visualization.
        """
        if not self.model_loaded or self.model is None:
            return {
                "status": "unavailable",
                "error": "Image classification model is not loaded or configured.",
                "ai_generated_score": 0.0,
                "real_score": 0.0,
                "prediction": "unavailable",
                "confidence": 0.0,
                "grad_cam_overlay": None,
                "model_version": "EfficientNet-B0-TransferLearning-v1.0"
            }

        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

            # Predict logits
            with torch.no_grad():
                logits = self.model(input_tensor)
                probabilities = F.softmax(logits, dim=1).squeeze().cpu().numpy()

            real_score = float(probabilities[0])
            ai_score = float(probabilities[1])

            predicted_idx = 1 if ai_score >= self.ai_threshold else 0
            predicted_label = CLASS_NAMES[predicted_idx]

            # Generate Grad-CAM highlighting regions that influenced the AI-generated score
            grad_cam_overlay = None
            try:
                # Requires gradients for backward pass
                grad_tensor = input_tensor.clone().detach().requires_grad_(True)
                cam = self.grad_cam.generate_heatmap(grad_tensor, target_class=1)
                grad_cam_overlay = self.grad_cam.overlay_on_image(pil_img, cam)
            except Exception as cam_err:
                logger.warning(f"Grad-CAM generation failed: {str(cam_err)}")

            # Calibration note: raw softmax scores indicate model confidence, not guaranteed probability
            confidence = max(real_score, ai_score)

            return {
                "status": "completed",
                "prediction": predicted_label,
                "ai_generated_score": round(ai_score, 4),
                "real_score": round(real_score, 4),
                "confidence": round(confidence, 4),
                "ai_decision_threshold": round(self.ai_threshold, 4),
                "grad_cam_overlay": grad_cam_overlay,
                "model_version": "EfficientNet-B0-TransferLearning-v1.0",
                "image_dimensions": {"width": pil_img.width, "height": pil_img.height},
                "limitations": [
                    "Evaluates visual texture artifacts characteristic of generative diffusion and GAN synthesis.",
                    "Does not detect targeted deepfake facial swaps if the base frame is genuine photography.",
                    "High compression, re-encoding, or heavy social media filtering can cause false positives or false negatives."
                ]
            }
        except Exception as e:
            logger.error(f"Image inference error: {str(e)}")
            return {
                "status": "failed",
                "error": f"Image processing failed: {str(e)}",
                "prediction": "inconclusive",
                "ai_generated_score": 0.0,
                "real_score": 0.0,
                "confidence": 0.0,
                "grad_cam_overlay": None,
                "model_version": "EfficientNet-B0-TransferLearning-v1.0"
            }

image_detector_service = ImageDetectorService()
