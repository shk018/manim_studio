"""
Audio pipeline for Manim Studio: auto-narration (offline TTS via pyttsx3),
procedurally generated background music (original, synthesized — not
copyrighted samples), and muxing both into the rendered silent video.

Deliberately does NOT shell out to an external "ffmpeg" executable anywhere.
Manim itself renders video using the `av` (PyAV) library directly rather
than by calling an ffmpeg binary on PATH, so there's no guarantee ffmpeg is
installed or reachable on the machine at all — Manim working is not
evidence that "ffmpeg" as a command exists. This module uses the same `av`
library Manim already depends on for muxing, and pure Python (`wave` +
`numpy`) for audio mixing, so it works anywhere Manim itself works.
"""

import platform
import re
import wave
from pathlib import Path

import av
import numpy as np
import pyttsx3

_IS_WINDOWS = platform.system() == "Windows"
TARGET_SAMPLE_RATE = 44100


def _com_init():
    """On Windows, SAPI5 (pyttsx3's backend) requires COM to be initialized
    on whatever thread uses it. Our narration synthesis runs inside a
    background worker thread, not Python's main thread, and without this
    call pyttsx3 can fail silently or raise an obscure COM error there —
    which is a common cause of "narration/music just don't show up" on
    Windows. No-op on other platforms.
    """
    if _IS_WINDOWS:
        import pythoncom
        pythoncom.CoInitialize()


def _com_uninit():
    if _IS_WINDOWS:
        import pythoncom
        pythoncom.CoUninitialize()


# ---------------------------------------------------------------------------
# Voices
# ---------------------------------------------------------------------------

def get_available_voices():
    """List TTS voices installed on this machine.

    On Windows this reflects installed SAPI5 voices (commonly at least
    "Microsoft David" and "Microsoft Zira"). On macOS it reflects the
    built-in NSSpeechSynthesizer voices. On Linux it depends on espeak/
    espeak-ng being installed and may list many language variants.
    """
    engine = pyttsx3.init()
    voices = []
    try:
        _com_init()
        for v in engine.getProperty("voices"):
            voices.append({
                "id": v.id,
                "name": v.name or v.id,
            })
    finally:
        try:
            engine.stop()
        except Exception:
            pass
        _com_uninit()
    return voices


# ---------------------------------------------------------------------------
# Narration text
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"#\s*-{3,}\s*(?:\d+\.\s*)?(.+?)\s*-{3,}")


def extract_narration_segments(code: str):
    """Pull section headings out of comments like:

        # ---------- 2. Variables ----------

    and turn each into a short narration sentence. Returns a list of
    strings, one per detected section, in file order. Returns an empty
    list if the code has no such comment markers.
    """
    headings = []
    for match in _HEADING_RE.finditer(code):
        heading = match.group(1).strip()
        if heading and heading.lower() not in {h.lower() for h in headings}:
            headings.append(heading)

    if not headings:
        return []

    segments = []
    for i, heading in enumerate(headings):
        if i == 0:
            segments.append(f"Let's start with {heading.lower()}.")
        else:
            segments.append(f"Next, let's look at {heading.lower()}.")
    return segments


# ---------------------------------------------------------------------------
# Speech synthesis
# ---------------------------------------------------------------------------

def synthesize_speech(text: str, out_path: Path, voice_id: str = None, rate: int = 165):
    """Synthesize a single utterance to a wav file."""
    engine = pyttsx3.init()
    try:
        _com_init()
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", rate)
        engine.save_to_file(text, str(out_path))
        engine.runAndWait()
    finally:
        try:
            engine.stop()
        except Exception:
            pass
        _com_uninit()

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(
            f"TTS produced no audio file for voice_id={voice_id!r}. "
            f"This usually means the selected voice isn't actually installed, "
            f"or the speech engine failed silently."
        )


# ---------------------------------------------------------------------------
# WAV helpers (pure Python — no ffmpeg)
# ---------------------------------------------------------------------------

def _read_wav_mono(path: Path, target_sr: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """Read a 16-bit PCM wav file, downmix to mono, resample to target_sr,
    and return float32 samples normalized to [-1, 1]."""
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sampwidth != 2:
        raise RuntimeError(
            f"{path} is not 16-bit PCM (got {sampwidth * 8}-bit). "
            f"This TTS voice may be producing an unsupported audio format."
        )

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    if sr != target_sr and len(samples) > 1:
        duration = len(samples) / sr
        n_target = max(int(duration * target_sr), 1)
        x_old = np.linspace(0, duration, num=len(samples), endpoint=False)
        x_new = np.linspace(0, duration, num=n_target, endpoint=False)
        samples = np.interp(x_new, x_old, samples).astype(np.float32)

    return samples


def _write_wav_mono(samples: np.ndarray, out_path: Path, sample_rate: int = TARGET_SAMPLE_RATE):
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if peak > 1.0:
        samples = samples / peak
    int16 = (samples * 32767).astype(np.int16)
    with wave.open(str(out_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16.tobytes())


# ---------------------------------------------------------------------------
# Procedural background music
# ---------------------------------------------------------------------------

def generate_background_music(duration_seconds: float, out_path: Path,
                               sample_rate: int = TARGET_SAMPLE_RATE):
    """Generate an original ambient pad loop of the given duration.

    Fully synthesized (sine waves + a simple chord progression + fades) —
    no samples, no licensed audio, nothing sourced from the web.
    """
    chords = [
        [220.00, 277.18, 329.63],
        [196.00, 246.94, 293.66],
        [174.61, 220.00, 261.63],
        [164.81, 207.65, 246.94],
    ]
    chord_dur = 4.0
    total_samples = max(int(duration_seconds * sample_rate), 1)
    audio = np.zeros(total_samples, dtype=np.float32)

    t_cursor = 0.0
    chord_idx = 0
    while t_cursor < duration_seconds:
        seg_len = min(chord_dur, duration_seconds - t_cursor)
        n = int(seg_len * sample_rate)
        if n <= 0:
            break
        t = np.linspace(0, seg_len, n, endpoint=False)
        chord = chords[chord_idx % len(chords)]
        wave_seg = np.zeros(n, dtype=np.float32)
        for freq in chord:
            wave_seg += 0.15 * np.sin(2 * np.pi * freq * t)

        fade_len = int(0.3 * sample_rate)
        if n > 2 * fade_len:
            env = np.ones(n, dtype=np.float32)
            env[:fade_len] = np.linspace(0, 1, fade_len)
            env[-fade_len:] = np.linspace(1, 0, fade_len)
            wave_seg *= env

        start = int(t_cursor * sample_rate)
        end = min(start + n, total_samples)
        audio[start:end] += wave_seg[: end - start]

        t_cursor += chord_dur
        chord_idx += 1

    peak = np.max(np.abs(audio)) or 1.0
    audio = (audio / peak) * 0.5
    _write_wav_mono(audio, out_path, sample_rate)


# ---------------------------------------------------------------------------
# Duration (via PyAV — Manim's own video library, not ffmpeg)
# ---------------------------------------------------------------------------

def get_media_duration(path: Path) -> float:
    container = av.open(str(path))
    try:
        if container.duration:
            return float(container.duration) / av.time_base
        # Fall back to the video stream's own duration if the container
        # doesn't report one directly.
        stream = container.streams.video[0]
        if stream.duration:
            return float(stream.duration * stream.time_base)
        raise RuntimeError(f"Could not determine duration of {path}: no duration metadata found.")
    finally:
        container.close()


# ---------------------------------------------------------------------------
# Mixing (pure Python — no ffmpeg)
# ---------------------------------------------------------------------------

def build_audio_track(job_dir: Path, video_duration: float, narration_clips, add_music: bool) -> Path:
    """Build one mixed mono wav (narration segments at their start times,
    plus optional background music) matching video_duration.

    narration_clips is a list of (wav_path, start_time_seconds).
    """
    out_path = job_dir / "mixed_audio.wav"
    total_samples = max(int(video_duration * TARGET_SAMPLE_RATE), 1)
    acc = np.zeros(total_samples, dtype=np.float32)

    for clip_path, start_time in narration_clips:
        samples = _read_wav_mono(clip_path)
        start_i = max(int(start_time * TARGET_SAMPLE_RATE), 0)
        end_i = min(start_i + len(samples), total_samples)
        if end_i > start_i:
            acc[start_i:end_i] += samples[: end_i - start_i]

    if add_music:
        music_path = job_dir / "music.wav"
        generate_background_music(video_duration, music_path)
        music_samples = _read_wav_mono(music_path)
        n = min(len(music_samples), total_samples)
        acc[:n] += music_samples[:n] * 0.6

    _write_wav_mono(acc, out_path)
    return out_path


# ---------------------------------------------------------------------------
# Muxing (via PyAV — no ffmpeg)
# ---------------------------------------------------------------------------

def mux_audio_into_video(video_path: Path, audio_path: Path, out_path: Path):
    """Remux the silent video's existing video stream (no re-encode) together
    with a newly AAC-encoded audio stream built from audio_path."""
    with wave.open(str(audio_path), "rb") as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    pcm = np.frombuffer(raw, dtype=np.int16)
    layout = "mono" if n_channels == 1 else "stereo"

    in_container = av.open(str(video_path))
    try:
        in_video_stream = in_container.streams.video[0]
        out_container = av.open(str(out_path), mode="w")
        try:
            out_video_stream = out_container.add_stream_from_template(in_video_stream)
            out_audio_stream = out_container.add_stream("aac", rate=sr)
            out_audio_stream.layout = layout

            for packet in in_container.demux(in_video_stream):
                if packet.dts is None:
                    continue
                packet.stream = out_video_stream
                out_container.mux(packet)

            chunk_size = 1024
            for i in range(0, len(pcm), chunk_size):
                chunk = pcm[i:i + chunk_size]
                if len(chunk) == 0:
                    continue
                frame = av.AudioFrame.from_ndarray(
                    chunk.reshape(1, -1), format="s16", layout=layout
                )
                frame.sample_rate = sr
                frame.pts = i
                for out_packet in out_audio_stream.encode(frame):
                    out_container.mux(out_packet)

            for out_packet in out_audio_stream.encode(None):
                out_container.mux(out_packet)
        finally:
            out_container.close()
    finally:
        in_container.close()


def add_narration_and_music(
    job_dir: Path,
    silent_video_path: Path,
    code: str,
    narration_mode: str,
    custom_script: str,
    voice_id: str,
    add_music: bool,
) -> Path:
    """Top-level entry point: takes the silent rendered video and produces a
    new mp4 with narration and/or music muxed in. Returns the path to the
    final video (a new file; the silent original is left untouched).

    narration_mode: "auto" (derive segments from code comments), "custom"
    (use custom_script as one continuous narration), or "none".
    """
    video_duration = get_media_duration(silent_video_path)
    narration_clips = []

    if narration_mode == "custom" and custom_script.strip():
        clip_path = job_dir / "narration_0.wav"
        synthesize_speech(custom_script.strip(), clip_path, voice_id=voice_id)
        narration_clips.append((clip_path, 0.5))

    elif narration_mode == "auto":
        segments = extract_narration_segments(code)
        if segments:
            slot = video_duration / len(segments)
            for i, text in enumerate(segments):
                clip_path = job_dir / f"narration_{i}.wav"
                synthesize_speech(text, clip_path, voice_id=voice_id)
                start_time = i * slot + min(0.4, slot * 0.1)
                narration_clips.append((clip_path, start_time))

    if not narration_clips and not add_music:
        return silent_video_path

    mixed_audio_path = build_audio_track(job_dir, video_duration, narration_clips, add_music)
    final_path = job_dir / "final_with_audio.mp4"
    mux_audio_into_video(silent_video_path, mixed_audio_path, final_path)
    return final_path
