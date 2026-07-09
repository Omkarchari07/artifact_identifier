import os
import json
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from pathlib import Path

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
ACCURACY_PLOT_PATH = MODEL_DIR / "accuracy_plot.png"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

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

# =========================
# SAVE FINAL MODEL
# =========================

model.save(FINAL_MODEL_PATH)

print("\nTraining completed.")
print(f"Model saved as {FINAL_MODEL_PATH}")

# =========================
# PLOT ACCURACY
# =========================

acc = history1.history["accuracy"] + history2.history["accuracy"]
val_acc = history1.history["val_accuracy"] + history2.history["val_accuracy"]

plt.plot(acc, label="Train Accuracy")
plt.plot(val_acc, label="Validation Accuracy")

plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend()

plt.savefig(ACCURACY_PLOT_PATH)

print(f"Accuracy plot saved as {ACCURACY_PLOT_PATH}")