<div align="center">

# 🤟 SignScope

### Real-time sign language detection, right in your browser.

A lightweight Flask + CNN app that watches your webcam and reads back **Danger**, **Help**, or **Peace** hand signs live — no install, no cloud upload, no accounts.

<img width="1435" height="662" alt="image" src="https://github.com/user-attachments/assets/2c9c4e46-c7e3-4117-b6d3-0c07ea1a2051" />
<img width="1620" height="455" alt="image" src="https://github.com/user-attachments/assets/07665ac7-5a1c-47c3-add9-a77b4c02c0c1" />

##Prototype
<img width="1600" height="747" alt="image" src="https://github.com/user-attachments/assets/f16cb562-7ca5-4526-bcfc-9c1ef4acf68a" />
<img width="1600" height="745" alt="image" src="https://github.com/user-attachments/assets/c4752c1d-5d44-46e3-8d36-bd0a38b5624f" />
<img width="1600" height="743" alt="image" src="https://github.com/user-attachments/assets/df784bb1-333a-4845-9021-71c49b5cca52" />

</div>

---

## ✨ What it does

SignScope opens your webcam, crops a small region in the center of the frame, and feeds it — 3 to 4 times a second — into a 48×48 grayscale CNN classifier trained to recognize a handful of sign-language gestures. The result streams back as a live HUD: a big readout label, a confidence bar, and a rolling log of recent detections.

Everything runs on your own machine. Frames are classified and immediately discarded — nothing is saved, logged, or sent anywhere beyond your own Flask server.

## 🖼️ How it works

<p align="center">
  <img src="docs/images/architecture.svg" alt="SignScope request lifecycle: browser captures a frame, sends it to Flask, the model predicts, and the UI updates" width="100%">
</p>

Every prediction is a straight round trip: **capture → crop → encode → POST → decode → predict → respond → render.** No sessions, no database, no state kept between requests.

## 🚶 Using it

<p align="center">
  <img src="docs/images/workflow.svg" alt="User workflow: open the app, start the camera, allow permission, hold your hand in frame, see the live label" width="100%">
</p>

## 🚀 Getting started

```bash
git clone https://github.com/<your-username>/signscope.git
cd signscope
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**, click **Start camera**, allow camera access, and hold a hand sign inside the on-screen reticle.

> **Note:** the model weights (`model/*.h5`) are tracked with [Git LFS](https://git-lfs.com). Install Git LFS *before* cloning, or run `git lfs pull` afterward, so the ~48MB weights file comes down correctly instead of as a tiny pointer file.

## 🗂️ Project structure

```
signscope/
├── app.py                  # Flask app: loads the model, exposes /predict
├── requirements.txt
├── model/
│   ├── signlanguagedetectionmodel48x48.json   # Keras model architecture
│   └── signlanguagedetectionmodel48x48.h5     # Trained weights (Git LFS)
├── static/
│   ├── css/style.css       # HUD styling
│   └── js/main.js          # Webcam capture + prediction loop
├── templates/
│   └── index.html          # Single-page UI
└── docs/images/            # README diagrams
```

## 🧠 Model details

| | |
|---|---|
| **Input** | 48×48 grayscale image |
| **Classes** | `Danger`, `Help`, `Peace`, `blank` |
| **Confidence threshold** | 60% (below this, the UI shows no detection) |
| **Framework** | Keras / TensorFlow |

Retraining with different gestures? Update the `LABELS` list in `app.py` and the model's output layer size to match — they must stay in the same order the model was trained on.

## 🌐 Deploying beyond localhost

The dev server started by `python app.py` is for local use only. For a real deployment:

1. **Use a production WSGI server**, keeping a single worker so the model isn't loaded into memory multiple times:
   ```bash
   gunicorn -w 1 -b 0.0.0.0:8000 app:app
   ```
2. **Serve over HTTPS.** Browsers only grant webcam access (`getUserMedia`) on secure origins (`https://`) or `localhost` — plain `http://` on a public domain will silently fail to get camera permission.
3. **Good hosting fits:** Render, Railway, or Fly.io for a simple git-push deploy with HTTPS included; or a VM behind nginx + gunicorn + certbot if you want full control.
4. Check your host's upload/slug size limits — the model file is ~48MB.

## 🔒 Security notes

This project was reviewed before being made public. A few things worth knowing if you fork or extend it:

- **No secrets in this repo.** No API keys, credentials, or `.env` files are committed — a `.gitignore` is included to keep it that way.
- **Request size is capped** (`MAX_CONTENT_LENGTH` in `app.py`) so `/predict` can't be hammered with oversized payloads.
- **Errors are handled generically.** `/predict` never leaks stack traces or file paths back to the client, even on bad input.
- **`debug=False`** in the shipped `app.py` — never flip this to `True` on anything reachable from the internet; Flask's debugger allows remote code execution if it's ever exposed.
- **Dependencies are version-pinned** in `requirements.txt` rather than left fully open-ended, so installs are reproducible and don't silently pull in a newer, untested (or vulnerable) release.
- **No data leaves the server.** Frames are decoded, classified, and discarded per-request — nothing is written to disk or a database.
- If you add authentication, rate limiting, or logging on top of this, keep secrets in environment variables (or a secrets manager), never hardcoded — and make sure `.env` stays out of git via `.gitignore`.

## 🛣️ Ideas for extending this

- Add more gesture classes and retrain the model
- Rate-limit `/predict` per IP for public deployments
- Swap the polling loop for a WebSocket stream
- Add a confidence history chart alongside the log strip

## 📄 License

Released under the [MIT License](LICENSE) — use it, fork it, ship it.

---

<div align="center">
<sub>Built with Flask, Keras, and a webcam. No signs were harmed in the making of this project.</sub>
</div>
