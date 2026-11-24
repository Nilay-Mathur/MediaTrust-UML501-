import os
import sys
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.ml.image_detector.model import EfficientNetDeepfakeDetector

class ImageFolderBinaryDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.samples = []
        self.transform = transform
        
        real_dir = os.path.join(root_dir, "real")
        ai_dir = os.path.join(root_dir, "ai_generated")

        if os.path.exists(real_dir):
            for fname in os.listdir(real_dir):
                if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    self.samples.append((os.path.join(real_dir, fname), 0))  # 0: real_image

        if os.path.exists(ai_dir):
            for fname in os.listdir(ai_dir):
                if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    self.samples.append((os.path.join(ai_dir, fname), 1))  # 1: ai_generated

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, torch.tensor(label, dtype=torch.long)

def train_image_detector(epochs=3, batch_size=4, lr=1e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training EfficientNet-B0 Deepfake Detector on: {device}")

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "sample_data"))
    save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "efficientnet_b0_deepfake.pt"))
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    dataset = ImageFolderBinaryDataset(data_dir, transform=transform)
    if len(dataset) == 0:
        print("Error: No images found in dataset directory. Run generate_sample_fixtures.py first.")
        return

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model = EfficientNetDeepfakeDetector(num_classes=2, pretrained=True).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)

    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        epoch_loss = running_loss / total if total > 0 else 0
        epoch_acc = correct / total if total > 0 else 0
        print(f"Epoch [{epoch+1}/{epochs}] - Loss: {epoch_loss:.4f} - Training Accuracy: {epoch_acc*100:.2f}%")

    # Save checkpoint
    torch.save({
        "state_dict": model.state_dict(),
        "architecture": "EfficientNet-B0",
        "classes": ["real_image", "ai_generated"],
        "epochs_trained": epochs,
        "input_resolution": (224, 224)
    }, save_path)
    print(f"Model checkpoint successfully saved to {save_path}")

if __name__ == "__main__":
    train_image_detector(epochs=3)
