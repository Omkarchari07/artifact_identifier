from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from PIL import Image
import numpy as np
import tensorflow as tf
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

# =========================
# LOAD MODEL
# =========================

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "final_model.keras"
LABELS_PATH = MODEL_DIR / "labels.json"
ROOT_LABELS_PATH = BASE_DIR / "labels.json"
ARTIFACT_METADATA_DIR = BASE_DIR / "dataset_split" / "val"

model = tf.keras.models.load_model(MODEL_PATH)

# =========================
# LOAD LABELS
# =========================

labels_path = LABELS_PATH if LABELS_PATH.exists() else ROOT_LABELS_PATH

with open(labels_path, "r", encoding="utf-8") as f:
    CLASS_NAMES = json.load(f)


def load_artifact_database(metadata_root):

    database = {}

    if not metadata_root.exists():
        return database

    for class_folder in metadata_root.iterdir():
        if not class_folder.is_dir():
            continue

        preferred_path = class_folder / "info.json"

        if preferred_path.exists():
            json_path = preferred_path
        else:
            json_files = [path for path in class_folder.iterdir() if path.is_file() and path.suffix.lower() == ".json"]

            if len(json_files) != 1:
                continue

            json_path = json_files[0]

        with open(json_path, "r", encoding="utf-8") as f:
            database[class_folder.name] = json.load(f)

    return database


ARTIFACT_DATABASE = load_artifact_database(ARTIFACT_METADATA_DIR)

ARTIFACT_INDEX = {}


def normalize_label(label):

    return "".join(character.lower() for character in label if character.isalnum())


for key, value in ARTIFACT_DATABASE.items():
    ARTIFACT_INDEX.setdefault(normalize_label(key), (key, value))

IMG_SIZE = (224, 224)

# =========================
# IMAGE PREPROCESS
# =========================

def prepare_image(img):

    img = img.resize(IMG_SIZE)

    img = np.array(img).astype("float32")

    img = tf.keras.applications.efficientnet.preprocess_input(img)

    img = np.expand_dims(img, axis=0)

    return img


def lookup_artifact_info(class_name):

    normalized = normalize_label(class_name)

    match = ARTIFACT_INDEX.get(normalized)

    if match is None:
        return {
            "matched": False,
            "source_label": class_name,
            "title": class_name,
            "object_type": "",
            "main_material": "",
            "provenance": "",
            "style": "",
            "period": "",
            "tribe": "",
            "culture": "",
            "brief_description": "",
            "detailed_description": ""
        }

    source_label, artifact = match

    return {
        "matched": True,
        "source_label": source_label,
        "title": artifact.get("title", class_name),
        "object_type": artifact.get("object_type", ""),
        "main_material": artifact.get("main_material", ""),
        "provenance": artifact.get("provenance", ""),
        "style": artifact.get("style", ""),
        "period": artifact.get("period", ""),
        "tribe": artifact.get("tribe", ""),
        "culture": artifact.get("culture", ""),
        "brief_description": artifact.get("brief_description", ""),
        "detailed_description": artifact.get("detailed_description", "")
    }

# =========================
# PREDICT ROUTE
# =========================

@app.route("/predict", methods=["POST"])
def predict():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    img = Image.open(file.stream).convert("RGB")

    img = prepare_image(img)

    preds = model.predict(img)[0]

    top_idx = int(np.argmax(preds))

    top_class = CLASS_NAMES[top_idx]

    top_conf = float(preds[top_idx])
    top_info = lookup_artifact_info(top_class)

    # Top 5 predictions
    top_5_idx = np.argsort(preds)[::-1][:5]

    top_k = []

    for i in top_5_idx:
        class_name = CLASS_NAMES[int(i)]

        top_k.append({
            "class": class_name,
            "probability": float(preds[i]),
            "artifact_info": lookup_artifact_info(class_name)
        })

    return jsonify({
        "top1": {
            "class": top_class,
            "probability": top_conf,
            "artifact_info": top_info
        },
        "top_k": top_k
    })

# =========================
# HOME ROUTE
# =========================

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/sample_app.js")
def sample_app_script():
    return send_from_directory(BASE_DIR, "sample_app.js")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(BASE_DIR / "assets", filename)

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)
