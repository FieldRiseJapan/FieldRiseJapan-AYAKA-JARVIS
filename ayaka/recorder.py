from pathlib import Path
import wave

from .devices import query_wasapi_input


def record_wav(output_path: Path, audio_config) -> Path:
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Install numpy and sounddevice before recording") from exc

    device = query_wasapi_input(audio_config)
    samplerate = int(device.get("default_samplerate") or audio_config.sample_rate)
    frames = int(samplerate * audio_config.chunk_seconds)
    recording = sd.rec(
        frames,
        samplerate=samplerate,
        channels=audio_config.channels,
        dtype="int16",
        device=device["index"],
    )
    sd.wait()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(audio_config.channels)
        wav.setsampwidth(np.dtype("int16").itemsize)
        wav.setframerate(samplerate)
        wav.writeframes(recording.tobytes())
    return output_path
