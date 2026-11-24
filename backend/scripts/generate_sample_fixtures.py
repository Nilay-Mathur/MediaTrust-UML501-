import os
import numpy as np
from PIL import Image, ImageDraw

def generate_fixtures():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "sample_data")
    real_dir = os.path.join(data_dir, "real")
    ai_dir = os.path.join(data_dir, "ai_generated")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(ai_dir, exist_ok=True)

    print("Generating fixture images for testing and reproducible training...")

    # Generate 10 naturalistic pattern images (simulating natural photography textures)
    for i in range(10):
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        # Natural gradients and smooth organic curves
        for y in range(224):
            for x in range(224):
                arr[y, x, 0] = int(128 + 60 * np.sin(x / 20.0))
                arr[y, x, 1] = int(128 + 60 * np.cos(y / 20.0))
                arr[y, x, 2] = int(100 + 40 * np.sin((x + y) / 30.0))
        img = Image.fromarray(arr)
        draw = ImageDraw.Draw(img)
        draw.ellipse([30 + i*5, 30 + i*5, 120 + i*5, 120 + i*5], fill=(200, 150, 100))
        img.save(os.path.join(real_dir, f"real_{i:02d}.jpg"), "JPEG", quality=90)

    # Generate 10 synthetic pattern images (simulating diffusion high-frequency grid & checkerboard artifacts)
    for i in range(10):
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        # High-frequency lattice and checkerboard pattern
        for y in range(224):
            for x in range(224):
                val = 255 if ((x // (4 + i)) % 2 == (y // (4 + i)) % 2) else 30
                arr[y, x, 0] = val
                arr[y, x, 1] = (val + 100) % 256
                arr[y, x, 2] = (255 - val)
        img = Image.fromarray(arr)
        img.save(os.path.join(ai_dir, f"ai_{i:02d}.jpg"), "JPEG", quality=90)

    print(f"Sample test fixtures successfully created in {data_dir}")

if __name__ == "__main__":
    generate_fixtures()
