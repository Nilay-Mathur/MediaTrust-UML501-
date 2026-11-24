import io
import base64
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import numpy as np

CLASS_NAMES = ["real_image", "ai_generated"]

class EfficientNetDeepfakeDetector(nn.Module):
    """
    EfficientNet-B0 transfer learning architecture for detecting AI-generated synthetic imagery.
    Replaces the 1000-class ImageNet head with a 2-class binary classification head with dropout.
    """
    def __init__(self, num_classes: int = 2, pretrained: bool = True):
        super().__init__()
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        self.backbone = models.efficientnet_b0(weights=weights)

        # Freeze early layers for transfer learning stability
        for param in list(self.backbone.parameters())[:-20]:
            param.requires_grad = False

        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=False),
            nn.Linear(in_features, 128),
            nn.ReLU(inplace=False),
            nn.Dropout(p=0.2, inplace=False),
            nn.Linear(128, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def get_final_conv_layer(self):
        """Returns the final convolutional block in the feature extractor for Grad-CAM."""
        return self.backbone.features[-1]


class GradCAM:
    """
    Grad-CAM implementation for visualizing influential regions in EfficientNet-B0.
    """
    def __init__(self, model: EfficientNetDeepfakeDetector):
        self.model = model
        self.gradient = None
        self.activations = None
        self.hook_layers()

    def hook_layers(self):
        target_layer = self.model.get_final_conv_layer()

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradient = grad_out[0].detach()

        target_layer.register_forward_hook(forward_hook)
        target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor: torch.Tensor, target_class: int = 1) -> np.ndarray:
        self.model.eval()
        self.model.zero_grad()

        output = self.model(input_tensor)
        target = output[0, target_class]
        target.backward()

        if self.gradient is None or self.activations is None:
            return np.zeros((224, 224), dtype=np.float32)

        # Global average pooling of gradients
        weights = torch.mean(self.gradient, dim=[2, 3], keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1).squeeze().cpu().numpy()

        # Apply ReLU to focus on positive contributions
        cam = np.maximum(cam, 0)
        if np.max(cam) > 0:
            cam = cam / np.max(cam)

        return cam

    def overlay_on_image(self, original_img: Image.Image, cam: np.ndarray) -> str:
        """
        Resizes heatmap to original image dimension, applies a heatmap color palette,
        and returns base64 PNG data URL.
        """
        cam_resized = Image.fromarray((cam * 255).astype(np.uint8)).resize(original_img.size, Image.BILINEAR)
        cam_arr = np.array(cam_resized, dtype=np.float32) / 255.0

        orig_arr = np.array(original_img.convert("RGB"), dtype=np.float32)

        # Generate a colormap: Red for high activation, Blue for low
        heatmap = np.zeros_like(orig_arr)
        heatmap[:, :, 0] = cam_arr * 255.0          # Red
        heatmap[:, :, 2] = (1.0 - cam_arr) * 180.0  # Blue

        # Alpha blend 50% heatmap, 50% original image
        blended = (0.55 * orig_arr + 0.45 * heatmap).clip(0, 255).astype(np.uint8)

        buffered = io.BytesIO()
        Image.fromarray(blended).save(buffered, format="JPEG", quality=85)
        encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
