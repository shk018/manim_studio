# Manim Studio

A small local website: paste Manim scene code (and an optional note about what
it's for), click **Render video**, and get back an mp4 rendered by
[Manim Community](https://www.manim.community/) + ffmpeg.

## What you need on your machine

Manim renders text and math using Cairo/Pango, so a couple of system libraries
are required in addition to Python packages.

**macOS**
```bash
brew install ffmpeg cairo pango pkg-config
```

**Ubuntu / Debian**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev build-essential
```

**Windows**
Easiest path is WSL2 (Ubuntu) and following the Ubuntu instructions above.
Native Windows works too, but requires MiKTeX (for LaTeX-based `MathTex`)
and manual Cairo/Pango setup — see the
[Manim install docs](https://docs.manim.community/en/stable/installation.html).

Optional: install a LaTeX distribution (e.g. `texlive` or MiKTeX) if your
scenes use `MathTex`/`Tex`. Scenes that only use `Text` don't need it.

## Important: keep debug mode off

The server runs with Flask's debug/auto-reloader **off** by default, and this
matters more than usual for this app: Manim writes hundreds of temporary
files per render into `jobs/<job_id>/media/...`, which lives inside this
project folder. If the auto-reloader is on, Flask restarts the whole server
every time one of those temp files is written — killing your render mid-way,
wiping the job from memory, and leaving the page stuck on "Rendering…"
forever with no error. If you ever need debug mode for development, set
`FLASK_DEBUG=1` as an environment variable rather than editing `app.py`
directly, and expect renders to break while it's on.

## Auto narration and background music

The app can add voiceover narration and/or an original background music bed
to your rendered video.

**Narration modes** (pick one in the UI):
- **No narration** — just the silent video, as before.
- **Auto (from code comments)** — the app looks for section-heading comments
  in your code shaped like `# ---------- 2. Variables ----------` and turns
  each one into a short spoken line ("Let's start with variables.", "Next,
  let's look at operators.", ...), spaced evenly across the video's runtime.
  If your code has no comments in that shape, auto mode finds nothing to say
  and the video comes back silent (or music-only, if you also enabled
  music) — it does not invent narration from scratch.
- **Write my own script** — type any text and it's synthesized as one
  continuous narration track starting a moment after the video begins. This
  is the more reliable option if you want narration that actually explains
  the content, since auto-narration only knows section titles, not what's
  actually happening on screen.

**Voice**: the dropdown lists whatever text-to-speech voices are installed
on *your* machine (via `pyttsx3`, fully offline — no API keys, no internet
required, nothing sent anywhere):
- **Windows**: your installed SAPI5 voices, typically at least "Microsoft
  David" (male) and "Microsoft Zira" (female) out of the box.
- **macOS**: the built-in system voices (Settings → Accessibility → Spoken
  Content has more you can download).
- **Linux**: requires `espeak` or `espeak-ng` installed
  (`sudo apt install espeak-ng`), and will otherwise show no voices.

**Background music**: an original ambient pad, generated fresh for every
render by synthesizing sine-wave chords in Python (`audio_tools.py`) — not
a licensed sample or anything pulled from the internet. It's deliberately
quiet, mixed underneath narration.

**How it fits together**: narration timing is *approximate*, not frame-perfect.
Auto mode assumes each section gets an equal slice of the total video
duration; if a spoken line runs longer than its slice, it just continues
talking into the next section rather than getting cut off. For anything
where exact timing matters, write a custom script sized to roughly match
the video's pacing, or don't rely on narration timing being frame-accurate
this way — true per-animation sync would need rewriting your code around
the `manim-voiceover` library's `self.voiceover(...)` API, which is a
bigger change to how the code itself is structured.

## Setup

```bash
cd manim-studio
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## How to use it

1. (Optional) Write a short note in the top field — just a label for your own
   reference, it isn't used to generate or alter code.
2. Paste your Manim scene code into the code box. It must define at least one
   `class SomeName(Scene):` with a `construct(self)` method — that's the
   scene that gets rendered.
3. Pick a quality:
   - **draft** (480p) — fastest, good while you're iterating
   - **standard** (720p)
   - **final** (1080p) — slowest, use for the final export
4. Click **Render video**. The app runs `manim` in the background and polls
   for completion; when it's done the video plays inline and gets added to
   your render history (left sidebar-style list) so you can flip back to
   earlier renders in the same session.
5. If your code has a bug, the render log (Manim/Python's own error output)
   is shown directly under the code box instead of a video.

## Example scene to try first

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(BLUE, opacity=0.5)
        text = Text("Hello Manim").next_to(circle, UP)
        self.play(Create(circle), Write(text))
        self.play(circle.animate.shift(RIGHT * 2))
        self.wait(1)
```

## Architecture notes / how it works

- `app.py` — Flask server. `/api/render` writes your code to a per-job folder,
  runs `manim <quality flag> scene.py <SceneName>` as a subprocess, and copies
  the resulting mp4 into `renders/`. Rendering happens in a background thread
  so the request returns immediately with a `job_id`.
- `/api/status/<job_id>` — poll this for job status (`queued` → `rendering` →
  `done`/`error`), returned to the browser every 1.5s until it resolves.
- `/api/history` — last 50 jobs (in-memory; resets when the server restarts).
- `templates/index.html`, `static/style.css`, `static/script.js` — the UI.

## Extending it

- **Multiple scenes per file**: if your code defines more than one `Scene`
  subclass, the app currently renders the first one it finds. You can pass a
  specific one via the JSON body's `"scene"` field if you extend the UI with a
  scene picker (the backend already supports it — see `find_scene_class` and
  the `requested_scene` handling in `app.py`).
- **Persistence across restarts**: swap the in-memory `JOBS` dict for a small
  SQLite table or a file-backed store.
- **Multi-user / production use**: move rendering off background threads and
  into a real task queue (Celery/RQ + Redis), add auth, and put the render
  subprocess in a resource-limited sandbox (CPU/time/memory caps) since it
  executes arbitrary Python.
- **Code execution safety**: this app runs whatever Python you paste in with
  no sandboxing beyond a 5-minute timeout. That's fine for personal local use;
  don't expose this server to the open internet as-is.
