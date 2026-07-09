import os
from PIL import Image, ImageOps
from tqdm import tqdm

INPUT_DIR = "dataset"
OUTPUT_DIR = "dataset_224"

IMG_SIZE = 224

os.makedirs(OUTPUT_DIR, exist_ok=True)

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")


def process_image(input_path, output_path):
    try:
        img = Image.open(input_path).convert("RGB")

        # Maintain aspect ratio using padding
        img.thumbnail((IMG_SIZE, IMG_SIZE))

        # Create square background
        new_img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (0, 0, 0))

        # Center image
        x = (IMG_SIZE - img.width) // 2
        y = (IMG_SIZE - img.height) // 2

        new_img.paste(img, (x, y))

        # Save compressed JPEG
        new_img.save(output_path, "JPEG", quality=90)

    except Exception as e:
        print(f"Error processing {input_path}: {e}")


for class_name in os.listdir(INPUT_DIR):

    class_input = os.path.join(INPUT_DIR, class_name)

    if not os.path.isdir(class_input):
        continue

    class_output = os.path.join(OUTPUT_DIR, class_name)
    os.makedirs(class_output, exist_ok=True)

    images = [
        f for f in os.listdir(class_input)
        if f.lower().endswith(VALID_EXTENSIONS)
    ]

    for image_name in tqdm(images, desc=class_name):

        input_path = os.path.join(class_input, image_name)

        output_name = os.path.splitext(image_name)[0] + ".jpg"

        output_path = os.path.join(class_output, output_name)

        process_image(input_path, output_path)

print("\nDone preprocessing dataset.")