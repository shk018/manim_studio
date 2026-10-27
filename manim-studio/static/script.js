const renderBtn = document.getElementById("renderBtn");
const codeEl = document.getElementById("code");
const promptEl = document.getElementById("prompt");
const qualityEl = document.getElementById("quality");
const logEl = document.getElementById("log");
const sceneHintEl = document.getElementById("sceneHint");
const previewArea = document.getElementById("previewArea");
const historyList = document.getElementById("historyList");
const narrationScriptEl = document.getElementById("narrationScript");
const voiceSelectEl = document.getElementById("voiceSelect");
const musicToggleEl = document.getElementById("musicToggle");
const narrationModeRadios = document.querySelectorAll('input[name="narrationMode"]');

let pollTimer = null;

function getNarrationMode() {
  const checked = document.querySelector('input[name="narrationMode"]:checked');
  return checked ? checked.value : "none";
}

function updateNarrationScriptVisibility() {
  narrationScriptEl.classList.toggle("hidden", getNarrationMode() !== "custom");
}

narrationModeRadios.forEach((radio) => {
  radio.addEventListener("change", updateNarrationScriptVisibility);
});

async function loadVoices() {
  try {
    const res = await fetch("/api/voices");
    const data = await res.json();
    voiceSelectEl.innerHTML = "";

    if (!data.voices || data.voices.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No voices found on this system";
      opt.value = "";
      voiceSelectEl.appendChild(opt);
      voiceSelectEl.disabled = true;
      return;
    }

    data.voices.forEach((voice) => {
      const opt = document.createElement("option");
      opt.value = voice.id;
      opt.textContent = voice.name;
      voiceSelectEl.appendChild(opt);
    });
    voiceSelectEl.disabled = false;
  } catch (err) {
    voiceSelectEl.innerHTML = '<option value="">Couldn\'t load voices</option>';
    voiceSelectEl.disabled = true;
  }
}

function setBusy(busy, label) {
  renderBtn.disabled = busy;
  renderBtn.textContent = busy ? (label || "Rendering…") : "Render video";
}

function showLog(text) {
  if (!text) {
    logEl.classList.add("hidden");
    logEl.textContent = "";
    return;
  }
  logEl.classList.remove("hidden");
  logEl.textContent = text;
}

function showVideo(url) {
  previewArea.innerHTML = `<video src="${url}" controls autoplay loop></video>`;
}

function showEmptyPreview() {
  previewArea.innerHTML = `
    <div class="preview-empty">
      <span class="preview-empty-icon">&#9655;</span>
      <p>Your rendered video will appear here.</p>
    </div>`;
}

async function startRender() {
  const code = codeEl.value.trim();
  if (!code) {
    showLog("Paste some Manim scene code first.");
    return;
  }

  setBusy(true);
  showLog("");
  sceneHintEl.textContent = "";

  try {
    const res = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        prompt: promptEl.value.trim(),
        quality: qualityEl.value,
        narration_mode: getNarrationMode(),
        narration_script: narrationScriptEl.value,
        voice_id: voiceSelectEl.value || null,
        add_music: musicToggleEl.checked,
      }),
    });
    const data = await res.json();

    if (!res.ok) {
      showLog(data.error || "Something went wrong submitting the render.");
      setBusy(false);
      return;
    }

    sceneHintEl.textContent = `Rendering scene: ${data.scene}` +
      (data.scenes_found.length > 1 ? ` (found ${data.scenes_found.length} scenes, using the first)` : "");

    pollJob(data.job_id);
  } catch (err) {
    showLog("Network error: " + err.message);
    setBusy(false);
  }
}

const POLL_INTERVAL_MS = 1500;
const MAX_MISSED_POLLS = 5; // tolerate a few transient failures before giving up

function pollJob(jobId) {
  if (pollTimer) clearInterval(pollTimer);
  let missedPolls = 0;

  pollTimer = setInterval(async () => {
    let res, job;
    try {
      res = await fetch(`/api/status/${jobId}`);
    } catch (err) {
      // Network error (e.g. server briefly unreachable) — count it and keep trying.
      missedPolls += 1;
      if (missedPolls >= MAX_MISSED_POLLS) {
        clearInterval(pollTimer);
        setBusy(false);
        showLog(`Lost connection to the server while polling for job ${jobId}. ` +
                `Check that the Flask server is still running.`);
      }
      return;
    }

    if (res.status === 404) {
      // The job no longer exists server-side — most commonly because the
      // Flask server restarted (e.g. debug/reloader was on) and its
      // in-memory job list was wiped. Don't spin forever; tell the user.
      clearInterval(pollTimer);
      setBusy(false);
      showLog(
        `Job ${jobId} no longer exists on the server.\n\n` +
        `This usually means the Flask server restarted mid-render (for example, ` +
        `if debug mode / the auto-reloader is on — it restarts every time Manim ` +
        `writes a temp file). Make sure app.py is run with debug off, then try ` +
        `rendering again.`
      );
      return;
    }

    if (!res.ok) {
      missedPolls += 1;
      if (missedPolls >= MAX_MISSED_POLLS) {
        clearInterval(pollTimer);
        setBusy(false);
        showLog(`Server returned an unexpected error (HTTP ${res.status}) while checking job status.`);
      }
      return;
    }

    missedPolls = 0;
    job = await res.json();

    if (job.status === "adding_audio") {
      setBusy(true, "Adding narration/music…");
    } else if (job.status === "rendering") {
      setBusy(true, "Rendering…");
    }

    if (job.status === "done") {
      clearInterval(pollTimer);
      setBusy(false);
      showVideo(job.video_url);
      if (job.audio_status === "failed") {
        showLog(
          `Video rendered, but adding narration/music failed — showing the silent video instead.\n\n` +
          `Error: ${job.audio_message || "unknown error"}\n\n` +
          (job.log || "")
        );
      } else if (job.audio_status === "skipped") {
        showLog(`Note: ${job.audio_message}`);
      } else {
        showLog("");
      }
      loadHistory();
    } else if (job.status === "error") {
      clearInterval(pollTimer);
      setBusy(false);
      showLog(job.log || "Render failed — no details returned.");
      loadHistory();
    }
    // else: still queued/rendering — keep polling
  }, POLL_INTERVAL_MS);
}

function statusLabel(status) {
  switch (status) {
    case "done": return "ready";
    case "error": return "failed";
    case "rendering": return "rendering…";
    case "adding_audio": return "adding audio…";
    default: return "queued";
  }
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const jobs = await res.json();
  historyList.innerHTML = "";

  if (jobs.length === 0) {
    historyList.innerHTML = `<li class="history-item"><span class="h-status">No renders yet</span></li>`;
    return;
  }

  jobs.forEach((job) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `
      <span class="h-name">${job.scene || "scene"}</span>
      <span class="h-status ${job.status}">${statusLabel(job.status)}</span>
    `;
    if (job.status === "done" && job.video_url) {
      li.addEventListener("click", () => showVideo(job.video_url));
    } else if (job.status === "error") {
      li.addEventListener("click", () => showLog(job.log || "No log available."));
    }
    historyList.appendChild(li);
  });
}

renderBtn.addEventListener("click", startRender);
loadHistory();
loadVoices();
updateNarrationScriptVisibility();
