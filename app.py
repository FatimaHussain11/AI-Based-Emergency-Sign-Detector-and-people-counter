import base64
import io
import os

import numpy as np
from flask import Flask, render_template, request, jsonify
from PIL import Image

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
# Keeping this at module scope means the model loads once, when the Flask
# process starts, not on every request.

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
JSON_PATH = os.path.join(MODEL_DIR, "signlanguagedetectionmodel48x48.json")
WEIGHTS_PATH = os.path.join(MODEL_DIR, "signlanguagedetectionmodel48x48.h5")

# Must match the class order the model was trained on.
LABELS = ["Danger", "Help", "Peace", "blank"]
CONFIDENCE_THRESHOLD = 60  # percent

app = Flask(__name__)

# Reject request bodies over ~2MB. A 48x48 crop encoded as base64 JPEG is a
# few KB at most, so this only exists to stop someone from POSTing a huge
# payload at /predict and tying up the server (basic DoS hardening).
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

print("Loading model...")
from keras.models import model_from_json  # noqa: E402  (import after app setup is fine)

with open(JSON_PATH, "r") as json_file:
    model_json = json_file.read()

model = model_from_json(model_json)
model.load_weights(WEIGHTS_PATH)
print("Model loaded.")


def preprocess(pil_image: Image.Image) -> np.ndarray:
    """Match the exact preprocessing used in realtimedetecttion.py:
    grayscale, 48x48, reshaped to (1, 48, 48, 1), scaled to [0, 1]."""
    gray = pil_image.convert("L")
    gray = gray.resize((48, 48))
    arr = np.array(gray, dtype="float32") / 255.0
    arr = arr.reshape(1, 48, 48, 1)
    return arr


def decode_base64_image(data_url: str) -> Image.Image:
    """Strip the 'data:image/jpeg;base64,' prefix and decode to a PIL image."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    image_bytes = base64.b64decode(data_url)
    return Image.open(io.BytesIO(image_bytes))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True)
    if not payload or "image" not in payload:
        return jsonify({"error": "No image received"}), 400

    try:
        pil_image = decode_base64_image(payload["image"])
        processed = preprocess(pil_image)
        prediction = model.predict(processed, verbose=0)
    except Exception:
        # Never leak internals (stack traces, file paths) to the client -
        # log server-side if you add logging, but keep the response generic.
        return jsonify({"error": "Could not process image"}), 400

    class_index = int(np.argmax(prediction))
    label = LABELS[class_index]
    confidence = float(np.max(prediction) * 100)

    return jsonify({"label": label, "confidence": confidence})


if __name__ == "__main__":
    # debug=True is handy locally; turn it off before any real deployment.
    app.run(host="0.0.0.0", port=5000, debug=False)
