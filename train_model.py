"""
Trains the sign-language CNN used by app.py.

Expects a dataset laid out like:
    <DATASET_DIR>/train/<class_name>/*.png
    <DATASET_DIR>/val/<class_name>/*.png

Set DATASET_DIR (env var or edit the default below) to point at your own
copy of the dataset - nothing about your local machine or folder layout
is hardcoded here, so this is safe to publish.
"""

import os

from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import Conv2D, Dense, Dropout, Flatten, MaxPooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ---------------------------------------------------------------------------
# Config - override via environment variable, no personal paths committed
# ---------------------------------------------------------------------------
DATASET_DIR = os.environ.get("DATASET_DIR", "dataset")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")

BATCH_SIZE = 128
EPOCHS = 100
IMAGE_SIZE = (48, 48)

train_datagen = ImageDataGenerator(rescale=1.0 / 255)
val_datagen = ImageDataGenerator(rescale=1.0 / 255)

train_generator = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    color_mode="grayscale",
)

validation_generator = val_datagen.flow_from_directory(
    VAL_DIR,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    color_mode="grayscale",
)

# IMPORTANT: this order must match LABELS in app.py exactly, or predictions
# served by the Flask app will be mislabeled.
class_names = list(train_generator.class_indices.keys())
print("Classes (in training order):", class_names)
print("Copy this list into LABELS in app.py before deploying the model.")


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
num_classes = train_generator.num_classes

model = Sequential()

model.add(Conv2D(128, kernel_size=(3, 3), activation="relu", input_shape=(48, 48, 1)))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Conv2D(256, kernel_size=(3, 3), activation="relu"))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Conv2D(512, kernel_size=(3, 3), activation="relu"))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Conv2D(512, kernel_size=(3, 3), activation="relu"))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.4))

model.add(Flatten())

model.add(Dense(512, activation="relu"))
model.add(Dropout(0.4))
model.add(Dense(64, activation="relu"))
model.add(Dropout(0.2))
model.add(Dense(256, activation="relu"))
model.add(Dropout(0.3))
model.add(Dense(64, activation="relu"))
model.add(Dropout(0.2))
model.add(Dense(256, activation="relu"))
model.add(Dropout(0.3))

# Output layer size is derived from the dataset, so it always matches the
# number of classes found in DATASET_DIR/train instead of being hardcoded.
model.add(Dense(num_classes, activation="softmax"))

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

if __name__ == "__main__":
    tensorboard_callback = TensorBoard(log_dir="logs")
    model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // BATCH_SIZE,
        callbacks=[tensorboard_callback],
    )

    model.save_weights(os.path.join("model", "signlanguagedetectionmodel48x48.h5"))
    with open(os.path.join("model", "signlanguagedetectionmodel48x48.json"), "w") as f:
        f.write(model.to_json())
    print("Saved model weights and architecture to ./model/")
