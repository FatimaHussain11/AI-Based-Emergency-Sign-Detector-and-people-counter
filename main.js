// SignScope frontend logic
// Captures frames from the user's webcam, sends them to Flask's /predict
// endpoint, and renders the result as a live HUD readout.

const video = document.getElementById("video");
const captureCanvas = document.getElementById("captureCanvas");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const readoutValue = document.getElementById("readoutValue");
const confidenceFill = document.getElementById("confidenceFill");
const confidenceNum = document.getElementById("confidenceNum");
const logStrip = document.getElementById("logStrip");
const viewfinderHint = document.getElementById("viewfinderHint");

const PREDICT_INTERVAL_MS = 300; // ~3-4 predictions/sec, adjust as needed
const CONFIDENCE_THRESHOLD = 60; // must match backend intent, shown client-side too
const ROI_FRACTION = 0.72; // matches the reticle's inset(14%) box -> 100% - 2*14%

let stream = null;
let predictTimer = null;
let lastLoggedLabel = null;

function setStatus(state, text) {
  statusDot.classList.remove("ready", "error");
  if (state) statusDot.classList.add(state);
  statusText.textContent = text;
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    video.srcObject = stream;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    viewfinderHint.textContent = "Place your hand inside the frame";
    setStatus("ready", "Model ready — detecting");
    predictTimer = setInterval(captureAndPredict, PREDICT_INTERVAL_MS);
  } catch (err) {
    console.error(err);
    setStatus("error", "Camera access denied");
    viewfinderHint.textContent = "Couldn't access your camera";
  }
}

function stopCamera() {
  if (predictTimer) clearInterval(predictTimer);
  if (stream) stream.getTracks().forEach((t) => t.stop());
  stream = null;
  startBtn.disabled = false;
  stopBtn.disabled = true;
  setStatus(null, "Stopped");
  resetReadout();
}

function resetReadout() {
  readoutValue.textContent = "—";
  readoutValue.classList.remove("active");
  confidenceFill.style.width = "0%";
  confidenceNum.textContent = "0%";
}

function captureAndPredict() {
  if (!video.videoWidth) return;

  // Crop to the same square region the reticle highlights, so what the
  // model sees roughly matches what the user sees framed on screen.
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  const side = Math.min(vw, vh) * ROI_FRACTION;
  const sx = (vw - side) / 2;
  const sy = (vh - side) / 2;

  captureCanvas.width = 48;
  captureCanvas.height = 48;
  const ctx = captureCanvas.getContext("2d");

  // Undo the mirrored preview so the crop matches the real camera frame.
  ctx.save();
  ctx.translate(48, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(video, sx, sy, side, side, 0, 0, 48, 48);
  ctx.restore();

  const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.8);

  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: dataUrl }),
  })
    .then((res) => res.json())
    .then(handlePrediction)
    .catch((err) => {
      console.error("Prediction request failed:", err);
      setStatus("error", "Lost connection to server");
    });
}

function handlePrediction(data) {
  if (data.error) {
    setStatus("error", data.error);
    return;
  }

  const { label, confidence } = data;
  const pct = Math.round(confidence);

  confidenceFill.style.width = `${pct}%`;
  confidenceNum.textContent = `${pct}%`;

  if (label && label !== "blank" && confidence >= CONFIDENCE_THRESHOLD) {
    readoutValue.textContent = label;
    readoutValue.classList.add("active");
    logDetection(label);
  } else {
    readoutValue.textContent = "—";
    readoutValue.classList.remove("active");
  }
}

function logDetection(label) {
  if (label === lastLoggedLabel) return; // avoid spamming repeats
  lastLoggedLabel = label;

  const empty = logStrip.querySelector(".log-empty");
  if (empty) empty.remove();

  const chip = document.createElement("span");
  chip.className = "log-chip";
  chip.textContent = label;
  logStrip.prepend(chip);

  // keep the strip from growing forever
  while (logStrip.children.length > 12) {
    logStrip.removeChild(logStrip.lastChild);
  }
}

startBtn.addEventListener("click", startCamera);
stopBtn.addEventListener("click", stopCamera);

setStatus(null, "Click \u201cStart camera\u201d to begin");
