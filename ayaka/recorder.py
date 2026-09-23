from pathlib import Path
import wave

from .devices import query_wasapi_input
from .vad import VadSegmenter


def _write_wav(output_path: Path, recording, samplerate: int, channels: int) -> Path:
    import numpy as np

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(np.dtype("int16").itemsize)
        wav.setframerate(samplerate)
        wav.writeframes(recording.tobytes())
    return output_path


def _record_fixed(audio_config, device: dict, samplerate: int):
    import sounddevice as sd

    frames = int(samplerate * audio_config.chunk_seconds)
    print(f"🎙️ 録音開始（固定{audio_config.chunk_seconds}秒）", flush=True)
    recording = sd.rec(
        frames,
        samplerate=samplerate,
        channels=audio_config.channels,
        dtype="int16",
        device=device["index"],
    )
    sd.wait()
    print("⏹️ 録音終了", flush=True)
    return recording


def _record_vad(audio_config, vad_config, device: dict, samplerate: int):
    import numpy as np
    import sounddevice as sd

    block_frames = max(1, int(samplerate * vad_config.block_seconds))
    segmenter = VadSegmenter(vad_config, samplerate)
    print("🎧 音声待機中...", flush=True)
    with sd.InputStream(
        samplerate=samplerate,
        blocksize=block_frames,
        channels=audio_config.channels,
        dtype="int16",
        device=device["index"],
    ) as stream:
        while True:
            chunk, overflowed = stream.read(block_frames)
            if overflowed:
                print("⚠️ 音声入力バッファが一時的にあふれました", flush=True)
            values = np.asarray(chunk, dtype=np.int16).reshape(-1)
            was_waiting = segmenter.state == "waiting"
            segment = segmenter.feed(values)
            if segment is not None:
                print("⏹️ 発話終了を検出", flush=True)
                return segment.reshape(-1, 1)
            if was_waiting and segmenter.state == "recording":
                print("🎙️ 発話を検出しました", flush=True)
                print("🔴 録音中...", flush=True)


def record_wav(output_path: Path, audio_config, vad_config=None) -> Path | None:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Install numpy and sounddevice before recording") from exc

    device = query_wasapi_input(audio_config)
    samplerate = int(device.get("default_samplerate") or audio_config.sample_rate)
    if vad_config is not None and vad_config.enabled:
        recording = _record_vad(audio_config, vad_config, device, samplerate)
    else:
        recording = _record_fixed(audio_config, device, samplerate)
    return _write_wav(output_path, recording, samplerate, audio_config.channels)
