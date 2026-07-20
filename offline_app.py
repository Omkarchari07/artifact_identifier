from pathlib import Path
import json
import logging
import os
import time

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import numpy as np
from PIL import Image
import tensorflow as tf


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "final_model.keras"
LABELS_PATH = MODEL_DIR / "labels.json"
ROOT_LABELS_PATH = BASE_DIR / "labels.json"
ARTIFACT_METADATA_DIR = BASE_DIR / "dataset_split" / "val"
IMG_SIZE = (224, 224)


app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    app.logger.info("Loading local TensorFlow model from %s", MODEL_PATH)
    start_time = time.perf_counter()
    loaded_model = tf.keras.models.load_model(MODEL_PATH)
    app.logger.info("Model loaded in %.2f seconds", time.perf_counter() - start_time)

    return loaded_model


def load_class_names():
    labels_path = LABELS_PATH if LABELS_PATH.exists() else ROOT_LABELS_PATH

    if not labels_path.exists():
        raise FileNotFoundError(
            f"Labels file not found. Checked {LABELS_PATH} and {ROOT_LABELS_PATH}"
        )

    with open(labels_path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_model_labels(loaded_model, class_names):
    output_classes = loaded_model.output_shape[-1]

    if output_classes is not None and output_classes != len(class_names):
        raise ValueError(
            "Model output class count does not match labels.json. "
            f"Model outputs: {output_classes}, labels: {len(class_names)}. "
            "Use a model and labels file from the same training run."
        )


def load_artifact_database(metadata_root):
    database = {}

    if not metadata_root.exists():
        app.logger.warning("Artifact metadata folder not found: %s", metadata_root)
        return database

    for class_folder in metadata_root.iterdir():
        if not class_folder.is_dir():
            continue

        preferred_path = class_folder / "info.json"

        if preferred_path.exists():
            json_path = preferred_path
        else:
            json_files = [
                path for path in class_folder.iterdir()
                if path.is_file() and path.suffix.lower() == ".json"
            ]

            if len(json_files) != 1:
                continue

            json_path = json_files[0]

        with open(json_path, "r", encoding="utf-8") as file:
            database[class_folder.name] = json.load(file)

    return database


def normalize_label(label):
    return "".join(character.lower() for character in label if character.isalnum())


def build_artifact_index(database):
    artifact_index = {}

    for key, value in database.items():
        artifact_index.setdefault(normalize_label(key), (key, value))

    return artifact_index


def prepare_image(image):
    image = image.resize(IMG_SIZE)
    image = np.array(image).astype("float32")
    image = tf.keras.applications.efficientnet.preprocess_input(image)
    return np.expand_dims(image, axis=0)


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
            "detailed_description": "",
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
        "detailed_description": artifact.get("detailed_description", ""),
    }


MODEL = load_model()
CLASS_NAMES = load_class_names()
validate_model_labels(MODEL, CLASS_NAMES)

ARTIFACT_DATABASE = load_artifact_database(ARTIFACT_METADATA_DIR)
ARTIFACT_INDEX = build_artifact_index(ARTIFACT_DATABASE)
app.logger.info(
    "Loaded %d artifact metadata records from %s",
    len(ARTIFACT_DATABASE),
    ARTIFACT_METADATA_DIR,
)


def run_prediction():
    request_start = time.perf_counter()

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    uploaded_file = request.files["image"]

    try:
        image = Image.open(uploaded_file.stream).convert("RGB")
    except OSError:
        return jsonify({"error": "Uploaded file is not a valid image"}), 400

    prepared_image = prepare_image(image)
    predictions = MODEL.predict(prepared_image, verbose=0)[0]

    top_idx = int(np.argmax(predictions))
    top_class = CLASS_NAMES[top_idx]
    top_confidence = float(predictions[top_idx])

    top_k = []

    for index in np.argsort(predictions)[::-1][:5]:
        class_name = CLASS_NAMES[int(index)]
        top_k.append({
            "class": class_name,
            "probability": float(predictions[index]),
            "artifact_info": lookup_artifact_info(class_name),
        })

    app.logger.info(
        "Prediction completed in %.2f seconds: %s %.4f",
        time.perf_counter() - request_start,
        top_class,
        top_confidence,
    )

    return jsonify({
        "top1": {
            "class": top_class,
            "probability": top_confidence,
            "artifact_info": lookup_artifact_info(top_class),
        },
        "top_k": top_k,
    })


@app.route("/predict", methods=["POST"])
@app.route("/api/predict", methods=["POST"])
def predict():
    return run_prediction()


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/sample_app.js")
def sample_app_script():
    return send_from_directory(BASE_DIR, "sample_app.js")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(BASE_DIR / "assets", filename)


if __name__ == "__main__":
    port = int(os.environ.get("OFFLINE_PORT", os.environ.get("PORT", 5000)))
    app.logger.info("Starting offline app at http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=False)
