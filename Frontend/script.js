// frontend/script.js

const API_URL = "http://127.0.0.1:8000/compress";

const form = document.getElementById("compress-form");
const errorMessage = document.getElementById("error-message");
const resultDiv = document.getElementById("result");
const resultInfo = document.getElementById("result-info");
const resultPreview = document.getElementById("result-preview");
const downloadLink = document.getElementById("download-link");

let currentObjectUrl = null; // revoke the previous one on each new result, or blobs leak in memory

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  hideResult();

  const fileInput = document.getElementById("file");
  const outputFormat = document.getElementById("output_format").value;
  const targetKb = document.getElementById("target_kb").value;
  const targetPercent = document.getElementById("target_percent").value;
  const flip = document.getElementById("flip").value;
  const rotate = document.getElementById("rotate").value;

  if (!fileInput.files[0]) {
    showError("Choose a file first.");
    return;
  }

  // Same exactly-one-of check as main.py — catches the mistake before a
  // round trip. Backend still re-validates; this is just faster feedback.
  if ((targetKb === "") === (targetPercent === "")) {
    showError("Enter exactly one of target KB or target percent, not both or neither.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("output_format", outputFormat);

  if (targetKb !== "") {
    formData.append("target_kb", targetKb);
  } else {
    formData.append("target_percent", targetPercent);
  }

  // Skip empty flip/rotate entirely — an empty string matches neither
  // None (omission) nor a Literal value on the backend, so sending it
  // as "" would get rejected with a 422.
  if (flip !== "") formData.append("flip", flip);
  if (rotate !== "") formData.append("rotate", rotate);

  const submitButton = form.querySelector("button[type=submit]");
  submitButton.disabled = true;
  submitButton.textContent = "Compressing...";

  try {
    const response = await fetch(API_URL, { method: "POST", body: formData });

    if (!response.ok) {
      // HTTPException errors come back as JSON: {"detail": "..."} for
      // 400s, or {"detail": [...]} for 422 validation errors.
      const errorBody = await response.json();
      const detail = typeof errorBody.detail === "string"
        ? errorBody.detail
        : JSON.stringify(errorBody.detail);
      throw new Error(detail);
    }

    // Custom headers only readable here because main.py's CORS middleware
    // set expose_headers — otherwise the browser silently hides them.
    const finalQuality = response.headers.get("X-Final-Quality");
    const finalSizeBytes = response.headers.get("X-Final-Size-Bytes");
    const blob = await response.blob();

    if (currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = URL.createObjectURL(blob);

    resultPreview.src = currentObjectUrl;
    downloadLink.href = currentObjectUrl;
    downloadLink.download = `compressed.${outputFormat}`;

    const finalSizeKb = (Number(finalSizeBytes) / 1024).toFixed(1);
    resultInfo.textContent = `Quality: ${finalQuality} — Size: ${finalSizeKb} KB`;

    showResult();
  } catch (err) {
    showError(err.message);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Compress";
  }
});

function showError(msg) { errorMessage.textContent = msg; errorMessage.hidden = false; }
function hideError() { errorMessage.hidden = true; }
function showResult() { resultDiv.hidden = false; }
function hideResult() { resultDiv.hidden = true; }