"""
Manim Studio — a small web app that turns Manim Python code into a rendered
animation video (mp4), in the style of programmatic math/code animation videos.

Run with:  python app.py
Then open: http://localhost:5000
"""

import json
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, render_template

import audio_tools

BASE_DIR = Path(__file__).resolve().parent
JOBS_DIR = BASE_DIR / "jobs"          # one folder per render job (scene code, logs)
RENDERS_DIR = BASE_DIR / "renders"    # final mp4 files, served to the browser
JOBS_DIR.mkdir(exist_ok=True)
RENDERS_DIR.mkdir(exist_ok=True)

# In-memory job store. Fine for a single-user local tool; swap for a DB/queue
# (e.g. Redis + RQ/Celery) if you need multi-user or persistence across restarts.
JOBS = {}
JOBS_LOCK = threading.Lock()

app = Flask(__name__)

# Quality presets map to Manim's built-in flags.
QUALITY_FLAGS = {
    "low": "-ql",       # 480p15  -> fast, good for iterating
    "medium": "-qm",    # 720p30
    "high": "-qh",      # 1080p60
}


def find_scene_class(code: str):
    """Find Scene subclass names defined in the user's code, in order of appearance."""
    return re.findall(r"class\s+(\w+)\s*\(\s*(?:\w+\.)*Scene\s*\)", code)


def run_render_job(job_id: str, code: str, scene_name: str, quality: str,
                    narration_mode: str = "none", custom_script: str = "",
                    voice_id: str = None, add_music: bool = False):
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    scene_path = job_dir / "scene.py"
    scene_path.write_text(code, encoding="utf-8")

    log_path = job_dir / "render.log"
    flag = QUALITY_FLAGS.get(quality, "-ql")

    cmd = [
        "manim", flag,
        "--media_dir", str(job_dir / "media"),
        str(scene_path), scene_name,
    ]

    with JOBS_LOCK:
        JOBS[job_id]["status"] = "rendering"

    # Force UTF-8 for the child process's own stdio. Manim's console output
    # (progress bars, rich-formatted tracebacks) uses box-drawing and other
    # non-ASCII characters; without this, Python on Windows defaults to the
    # legacy system codepage (cp1252) for a subprocess whose output is
    # redirected to a file, which can raise UnicodeEncodeError inside Manim
    # itself and silently kill the render.
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"

    try:
        with open(log_path, "w", encoding="utf-8") as logf:
            proc = subprocess.run(
                cmd,
                cwd=job_dir,
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=300,  # 5 minute safety cap per render
                env=child_env,
            )
        log_text = log_path.read_text(encoding="utf-8", errors="replace")

        if proc.returncode != 0:
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["log"] = log_text
            return

        # Find the rendered mp4 anywhere under the job's media dir.
        media_root = job_dir / "media" / "videos"
        mp4_files = list(media_root.rglob(f"{scene_name}.mp4")) if media_root.exists() else []
        if not mp4_files:
            mp4_files = list(media_root.rglob("*.mp4")) if media_root.exists() else []

        if not mp4_files:
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["log"] = log_text + "\n\n[No mp4 output found after render.]"
            return

        # Manim picks the highest-resolution / most-recent match.
        result_file = sorted(mp4_files, key=lambda p: p.stat().st_mtime)[-1]

        final_video_path = result_file
        if narration_mode != "none" or add_music:
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "adding_audio"
            try:
                final_video_path = audio_tools.add_narration_and_music(
                    job_dir=job_dir,
                    silent_video_path=result_file,
                    code=code,
                    narration_mode=narration_mode,
                    custom_script=custom_script,
                    voice_id=voice_id,
                    add_music=add_music,
                )
                with JOBS_LOCK:
                    if final_video_path == result_file:
                        # add_narration_and_music can legitimately return the
                        # silent video unchanged if auto mode found no
                        # section comments to narrate and music wasn't asked
                        # for either — that's not a failure, just nothing to add.
                        JOBS[job_id]["audio_status"] = "skipped"
                        JOBS[job_id]["audio_message"] = (
                            "Auto narration found no '# ---- Heading ----' style "
                            "comments in your code to narrate, and no music was requested."
                        )
                    else:
                        JOBS[job_id]["audio_status"] = "ok"
            except Exception as audio_exc:  # noqa: BLE001
                # Don't lose a good silent render just because audio failed —
                # fall back to the silent video, but make the failure visible
                # (both in the render log and as a dedicated status field) so
                # it isn't silently swallowed.
                audio_error_path = job_dir / "audio_error.log"
                audio_error_path.write_text(
                    f"{type(audio_exc).__name__}: {audio_exc}", encoding="utf-8"
                )
                log_text += f"\n\n[Audio step failed, falling back to silent video: {audio_exc}]"
                final_video_path = result_file
                with JOBS_LOCK:
                    JOBS[job_id]["audio_status"] = "failed"
                    JOBS[job_id]["audio_message"] = str(audio_exc)
        else:
            with JOBS_LOCK:
                JOBS[job_id]["audio_status"] = "not_requested"

        final_name = f"{job_id}.mp4"
        final_path = RENDERS_DIR / final_name
        final_path.write_bytes(final_video_path.read_bytes())

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["video_url"] = f"/videos/{final_name}"
            JOBS[job_id]["log"] = log_text

    except subprocess.TimeoutExpired:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["log"] = "Render timed out after 5 minutes."
    except Exception as exc:  # noqa: BLE001
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["log"] = f"Unexpected error: {exc}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/voices")
def api_voices():
    try:
        voices = audio_tools.get_available_voices()
        return jsonify({"voices": voices})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"voices": [], "error": str(exc)}), 200


@app.route("/api/render", methods=["POST"])
def api_render():
    data = request.get_json(force=True)
    code = (data.get("code") or "").strip()
    prompt = (data.get("prompt") or "").strip()
    quality = data.get("quality", "low")

    narration_mode = data.get("narration_mode", "none")  # "none" | "auto" | "custom"
    custom_script = (data.get("narration_script") or "").strip()
    voice_id = data.get("voice_id") or None
    add_music = bool(data.get("add_music", False))

    if narration_mode not in ("none", "auto", "custom"):
        narration_mode = "none"

    if not code:
        return jsonify({"error": "No code provided."}), 400

    scenes = find_scene_class(code)
    if not scenes:
        return jsonify({
            "error": "No Manim Scene class found. Your code must define a class "
                     "like `class MyScene(Scene):` with a `construct(self)` method."
        }), 400

    requested_scene = data.get("scene")
    scene_name = requested_scene if requested_scene in scenes else scenes[0]

    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {
            "id": job_id,
            "status": "queued",
            "prompt": prompt,
            "scene": scene_name,
            "scenes_found": scenes,
            "quality": quality,
            "narration_mode": narration_mode,
            "add_music": add_music,
            "created": time.time(),
            "log": "",
            "video_url": None,
        }

    thread = threading.Thread(
        target=run_render_job,
        args=(job_id, code, scene_name, quality, narration_mode, custom_script, voice_id, add_music),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id, "scene": scene_name, "scenes_found": scenes})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job id."}), 404
    return jsonify(job)


@app.route("/api/history")
def api_history():
    with JOBS_LOCK:
        jobs = sorted(JOBS.values(), key=lambda j: j["created"], reverse=True)
    return jsonify(jobs[:50])


@app.route("/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory(RENDERS_DIR, filename)


if __name__ == "__main__":
    # IMPORTANT: debug/reloader must stay off. Manim writes hundreds of temp
    # files per render into jobs/<id>/media/... inside this project folder.
    # Flask's auto-reloader watches the whole project for file changes and
    # restarts the server on every single one of those temp files, which
    # kills the in-progress render each time. use_reloader=False is a second
    # safety net in case FLASK_DEBUG ever gets set by accident.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode, use_reloader=False)
