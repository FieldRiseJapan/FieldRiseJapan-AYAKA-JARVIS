from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioConfig:
    device_name: str = "Jabra Speak2 40 MS"
    hostapi_name: str = "Windows WASAPI"
    device_index: int | None = None
    sample_rate: int = 16000
    channels: int = 1
    chunk_seconds: int = 5


@dataclass(frozen=True)
class WhisperConfig:
    executable: Path = Path("vendor/whisper.cpp/build/bin/Release/whisper-cli.exe")
    model: Path = Path("models/ggml-small.bin")
    language: str = "ja"
    chunk_seconds: int = 5
    temperature: float = 0.0


@dataclass(frozen=True)
class AppConfig:
    audio: AudioConfig = AudioConfig()
    whisper: WhisperConfig = WhisperConfig()
    wake_words: tuple[str, ...] = ("彩花",)
    reply_text: str = "はい、社長。"
