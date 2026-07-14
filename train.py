import os
import json
import time
import numpy as np
import tensorflow as tf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.metrics import (
    classification_report,
    ConfusionMatrixDisplay,
    confusion_matrix
)
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint
)

# =========================
# SETTINGS
# =========================

IMG_SIZE = 224
BATCH_SIZE = 8
EPOCHS_HEAD = 3
EPOCHS_FINE = 2

TRAIN_DIR = "dataset_split/train"
VAL_DIR = "dataset_split/val"
MODEL_DIR = Path("models")
BEST_MODEL_PATH = MODEL_DIR / "best_model.keras"
FINAL_MODEL_PATH = MODEL_DIR / "final_model.keras"
LABELS_PATH = MODEL_DIR / "labels.json"
RESULTS_DIR = Path("training_results")
ACCURACY_PLOT_PATH = RESULTS_DIR / "accuracy_plot.png"
LOSS_PLOT_PATH = RESULTS_DIR / "loss_plot.png"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.png"
CLASSIFICATION_REPORT_PATH = RESULTS_DIR / "classification_report.txt"
TRAINING_SUMMARY_PATH = RESULTS_DIR / "training_summary.txt"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# REPORTING HELPERS
# =========================

def get_combined_history(*histories):
    combined_history = {}

    for history in histories:
        for metric_name, values in history.history.items():
            combined_history.setdefault(metric_name, []).extend(values)

    return combined_history


def setup_plot_style():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.titlesize": 20,
        "axes.labelsize": 16,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "legend.fontsize": 13,
        "font.size": 13,
    })


def plot_training_metric(
    epochs,
    train_values,
    val_values,
    title,
    ylabel,
    output_path,
    ylim=None
):
    setup_plot_style()

    plt.figure(figsize=(11, 7))
    plt.plot(
        epochs,
        train_values,
        marker="o",
        linewidth=2.5,
        label=f"Training {ylabel}"
    )
    plt.plot(
        epochs,
        val_values,
        marker="o",
        linewidth=2.5,
        label=f"Validation {ylabel}"
    )

    plt.title(title, pad=16)
    plt.xlabel("Epoch Number")
    plt.ylabel(ylabel)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.xticks(epochs)
    plt.grid(True, linestyle="--", linewidth=0.8, alpha=0.65)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def save_training_plots(history, output_dir):
    epochs = np.arange(1, len(history["accuracy"]) + 1)

    plot_training_metric(
        epochs,
        history["accuracy"],
        history["val_accuracy"],
        "Model Accuracy During Training",
        "Accuracy",
        output_dir / "accuracy_plot.png",
        ylim=(0.0, 1.0)
    )

    plot_training_metric(
        epochs,
        history["loss"],
        history["val_loss"],
        "Model Loss During Training",
        "Loss",
        output_dir / "loss_plot.png"
    )


def get_validation_labels_and_predictions(model, validation_dataset):
    y_true = np.concatenate([
        np.argmax(labels.numpy(), axis=1)
        for _, labels in validation_dataset
    ])
    y_pred_probabilities = model.predict(validation_dataset)
    y_pred = np.argmax(y_pred_probabilities, axis=1)

    return y_true, y_pred


def save_confusion_matrix(y_true, y_pred, class_names, output_path):
    setup_plot_style()

    labels = np.arange(len(class_names))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    class_count = len(class_names)
    figure_size = max(12, min(0.45 * class_count, 34))

    fig, ax = plt.subplots(figsize=(figure_size, figure_size))
    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=class_names
    )
    display.plot(
        ax=ax,
        cmap="Blues",
        values_format="d",
        colorbar=True
    )

    ax.set_title("Validation Confusion Matrix", pad=18)
    ax.set_xlabel("Predicted Class")
    ax.set_ylabel("Actual Class")
    plt.setp(
        ax.get_xticklabels(),
        rotation=45 if class_count <= 25 else 90,
        ha="right",
        rotation_mode="anchor"
    )
    plt.setp(ax.get_yticklabels(), rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_classification_report(y_true, y_pred, class_names, output_path):
    labels = np.arange(len(class_names))
    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=class_names,
        digits=4,
        zero_division=0
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\nClassification Report:")
    print(report)


def format_training_time(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def save_training_summary(
    history,
    model_name,
    num_classes,
    train_image_count,
    val_image_count,
    image_size,
    batch_size,
    training_time_seconds,
    output_path
):
    summary = [
        "Training Summary",
        "================",
        f"Model name: {model_name}",
        f"Number of classes: {num_classes}",
        f"Number of training images: {train_image_count}",
        f"Number of validation images: {val_image_count}",
        f"Image size: {image_size} x {image_size}",
        f"Batch size: {batch_size}",
        f"Epochs: {len(history['accuracy'])}",
        f"Final Training Accuracy: {history['accuracy'][-1]:.4f}",
        f"Final Validation Accuracy: {history['val_accuracy'][-1]:.4f}",
        f"Final Training Loss: {history['loss'][-1]:.4f}",
        f"Final Validation Loss: {history['val_loss'][-1]:.4f}",
        f"Training time: {format_training_time(training_time_seconds)}",
        f"Training time (seconds): {training_time_seconds:.2f}",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))
        f.write("\n")

# =========================
# LOAD DATASETS
# =========================

train_ds = tf.keras.utils.image_dataset_from_directory(
    TRAIN_DIR,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode="categorical"
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    VAL_DIR,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode="categorical",
    shuffle=False
)

class_names = train_ds.class_names
NUM_CLASSES = len(class_names)
TRAIN_IMAGE_COUNT = len(train_ds.file_paths)
VAL_IMAGE_COUNT = len(val_ds.file_paths)

print("\nClasses:")
print(class_names)

# Save labels
with open(LABELS_PATH, "w", encoding="utf-8") as f:
    json.dump(class_names, f)

# =========================
# PERFORMANCE
# =========================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# =========================
# AUGMENTATION
# =========================

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.15),
    layers.RandomContrast(0.15),
])

# =========================
# MODEL
# =========================

base_model = EfficientNetB0(
    weights="imagenet",
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

base_model.trainable = False

inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))

x = data_augmentation(inputs)

x = tf.keras.applications.efficientnet.preprocess_input(x)

x = base_model(x, training=False)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(0.4)(x)

outputs = layers.Dense(NUM_CLASSES, activation="softmax")(x)

model = models.Model(inputs, outputs)

# =========================
# PHASE 1
# =========================

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-3),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

callbacks = [
    EarlyStopping(
        patience=5,
        restore_best_weights=True
    ),

    ReduceLROnPlateau(
        factor=0.2,
        patience=2,
        verbose=1
    ),

    ModelCheckpoint(
        str(BEST_MODEL_PATH),
        save_best_only=True,
        monitor="val_accuracy"
    )
]

print("\nTraining classifier head...\n")

training_start_time = time.perf_counter()

history1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_HEAD,
    callbacks=callbacks
)

# =========================
# PHASE 2 FINE-TUNING
# =========================

base_model.trainable = True

for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-5),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

print("\nFine-tuning model...\n")

history2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_FINE,
    callbacks=callbacks
)

training_time_seconds = time.perf_counter() - training_start_time

# =========================
# SAVE FINAL MODEL
# =========================

model.save(FINAL_MODEL_PATH)

print("\nTraining completed.")
print(f"Model saved as {FINAL_MODEL_PATH}")

# =========================
# TRAINING RESULTS
# =========================

combined_history = get_combined_history(history1, history2)
save_training_plots(combined_history, RESULTS_DIR)
save_training_summary(
    combined_history,
    "EfficientNetB0",
    NUM_CLASSES,
    TRAIN_IMAGE_COUNT,
    VAL_IMAGE_COUNT,
    IMG_SIZE,
    BATCH_SIZE,
    training_time_seconds,
    TRAINING_SUMMARY_PATH
)

y_true, y_pred = get_validation_labels_and_predictions(model, val_ds)
save_confusion_matrix(y_true, y_pred, class_names, CONFUSION_MATRIX_PATH)
save_classification_report(
    y_true,
    y_pred,
    class_names,
    CLASSIFICATION_REPORT_PATH
)

print(f"Accuracy plot saved as {ACCURACY_PLOT_PATH}")
print(f"Loss plot saved as {LOSS_PLOT_PATH}")
print(f"Confusion matrix saved as {CONFUSION_MATRIX_PATH}")
print(f"Classification report saved as {CLASSIFICATION_REPORT_PATH}")
print(f"Training summary saved as {TRAINING_SUMMARY_PATH}")
