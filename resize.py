import os
from PIL import Image
from pathlib import Path

INPUT_DIR = Path("dataset")
OUTPUT_DIR = Path("dataset1200")

OUTPUT_DIR.mkdir(exist_ok=True)

TARGET_SIZE = 1024 # minimum side resolution

for class_dir in INPUT_DIR.iterdir():
    if class_dir.is_dir():
        out_class = OUTPUT_DIR / class_dir.name
        out_class.mkdir(exist_ok=True)

        images = list(class_dir.glob("*"))
        print(f"Processing {class_dir.name}: {len(images)} images")

        for img_path in images:
            try:
                img = Image.open(img_path).convert("RGB")

                w, h = img.size

                # Resize only if image smaller than target
                if min(w, h) < TARGET_SIZE:
                    scale = TARGET_SIZE / min(w, h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)

                    img = img.resize((new_w, new_h), Image.LANCZOS)

                out_path = out_class / (img_path.stem + ".jpg")

                img.save(
                    out_path,
                    "JPEG",
                    quality=72,
                    optimize=True
                )

            except Exception as e:
                print("Skipping:", img_path, e)

print("Done. Output -> dataset1200/")