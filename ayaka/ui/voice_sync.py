"""Windows TTS WAV playback with a small, standard-library-only mouth envelope."""

from __future__ import annotations

import math
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import time
import wave
from collections.abc import Callable


WINDOW_SECONDS = 0.025
RMS_FLOOR = 0.015
RMS_PEAK_RATIO = 0.12
OPEN_HOLD_SECONDS = 0.08
CLOSED_HOLD_SECONDS = 0.06


def synthesize_wav_windows(text: str, output: Path) -> None:
    # Text goes through stdin, never into executable PowerShell source.
    path = str(output).replace("'", "''")
    script = (
        "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "try { $s.SetOutputToWaveFile('" + path + "'); "
        "$s.Speak([Console]::In.ReadToEnd()) } finally { $s.Dispose() }"
    )
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                   input=text, text=True, encoding="utf-8", check=True, capture_output=True)
    if not output.is_file() or output.stat().st_size <= 44:
        raise ValueError("TTS did not produce a WAV")


def _rms(data: bytes, width: int) -> float:
    if not data or width not in (1, 2, 3, 4) or len(data) % width:
        raise ValueError("unsupported or incomplete PCM data")
    total = 0.0
    if width == 1:
        samples = (byte - 128 for byte in data)
        scale = 128
    elif width == 3:
        samples = (int.from_bytes(data[i:i + 3], "little", signed=True) for i in range(0, len(data), 3))
        scale = 1 << 23
    else:
        count = len(data) // width
        samples = struct.unpack("<" + ("h" if width == 2 else "i") * count, data)
        scale = 1 << (width * 8 - 1)
    for sample in samples:
        total += (sample / scale) ** 2
    return math.sqrt(total / (len(data) // width))


def analyze_wav(path: Path) -> tuple[tuple[float, ...], float, float]:
    with wave.open(str(path), "rb") as source:
        if source.getcomptype() != "NONE" or source.getsampwidth() not in (1, 2, 3, 4):
            raise ValueError("TTS WAV must contain uncompressed PCM")
        rate, channels = source.getframerate(), source.getnchannels()
        if rate <= 0 or channels <= 0:
            raise ValueError("invalid WAV format")
        window_frames = max(1, round(rate * WINDOW_SECONDS))
        values = []
        while data := source.readframes(window_frames):
            values.append(_rms(data, source.getsampwidth()))
        duration = source.getnframes() / rate
    if not values or duration <= 0 or not all(math.isfinite(value) for value in values):
        raise ValueError("empty or invalid TTS envelope")
    threshold = max(RMS_FLOOR, max(values) * RMS_PEAK_RATIO)
    return tuple(values), duration, threshold


def play_wav_windows(path: Path) -> None:
    import winsound  # Windows only; import on use so headless tests can run.

    winsound.PlaySound(str(path), winsound.SND_FILENAME)


def speak_with_envelope(text: str, generation: int, events, fallback: Callable[[str], None]) -> None:
    """Prepare first, then publish playback timing; always complete and remove the WAV."""
    wav_path = None
    try:
        try:
            with tempfile.NamedTemporaryFile(prefix="ayaka-tts-", suffix=".wav", delete=False) as temp:
                wav_path = Path(temp.name)
            synthesize_wav_windows(text, wav_path)
            envelope = analyze_wav(wav_path)
            gate = threading.Event()
            events.put(("speech_prepared", (generation, gate)))
            if not gate.wait(timeout=5):
                return
            started_at = time.monotonic()
            events.put(("speech_started", (generation, envelope, started_at)))
            play_wav_windows(wav_path)
        except Exception:
            events.put(("speech_fallback", generation))
            try:
                fallback(text)
            except Exception:
                pass  # Both playback paths failed; UI still returns to CLOSED.
    finally:
        if wav_path is not None:
            try:
                wav_path.unlink(missing_ok=True)
            except OSError:
                pass
        events.put(("speech_complete", generation))
