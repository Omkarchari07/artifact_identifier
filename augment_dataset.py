import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from tqdm import tqdm


DATASET_PATH = Path(r"C:\Users\Death_Protocol\Documents\artifact_identifier\dataset_split\train")
OUTPUT_PATH = DATASET_PATH.parent / "aug_Train"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def increase_brightness(image):
    return ImageEnhance.Brightness(image).enhance(1.12)


def reduce_brightness(image):
    return ImageEnhance.Brightness(image).enhance(0.88)


def add_slight_noise(image):
    image_array = np.array(image).astype(np.int16)
    noise = np.random.normal(0, 8, image_array.shape).astype(np.int16)
    noisy_image = np.clip(image_array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_image)


def mirror_image(image):
    return ImageOps.mirror(image)


def augment_image(image):
    return {
        "bright": increase_brightness(image),
        "dark": reduce_brightness(image),
        "noise": add_slight_noise(image),
        "mirror": mirror_image(image),
    }


def is_image_file(path):
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {DATASET_PATH}")

    if OUTPUT_PATH.exists():
        shutil.rmtree(OUTPUT_PATH)

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    class_folders = sorted(
        path for path in DATASET_PATH.iterdir()
        if path.is_dir() and path.name != OUTPUT_PATH.name
    )

    for class_folder in class_folders:
        output_class_folder = OUTPUT_PATH / class_folder.name
        output_class_folder.mkdir(parents=True, exist_ok=True)

        image_paths = sorted(path for path in class_folder.iterdir() if is_image_file(path))

        for image_path in tqdm(image_paths, desc=class_folder.name):
            try:
                image = Image.open(image_path).convert("RGB")
            except OSError:
                continue

            original_output_path = output_class_folder / image_path.name
            image.save(original_output_path)

            for suffix, augmented_image in augment_image(image).items():
                save_path = output_class_folder / f"{image_path.stem}_{suffix}.jpg"
                augmented_image.save(save_path, quality=95)


if __name__ == "__main__":
    main()
