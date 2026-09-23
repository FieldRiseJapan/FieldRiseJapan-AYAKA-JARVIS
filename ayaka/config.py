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
class VadConfig:
    enabled: bool = True
    threshold: int = 500
    silence_seconds: float = 0.8
    pre_roll_seconds: float = 0.3
    max_record_seconds: float = 12.0
    block_seconds: float = 0.02


@dataclass(frozen=True)
class WhisperConfig:
    executable: Path = Path("vendor/whisper.cpp/build-release-x64/bin/whisper-cli.exe")
    model: Path = Path("vendor/whisper.cpp/ggml-small.bin")
    language: str = "ja"
    chunk_seconds: int = 5
    temperature: float = 0.0


@dataclass(frozen=True)
class AnimationConfig:
    breathing_enabled: bool = False
    breathing_amplitude_px: int = 1
    breathing_period_seconds: float = 4.0
    frame_interval_ms: int = 100

    @property
    def safe_breathing_amplitude_px(self) -> int:
        return min(2, max(0, self.breathing_amplitude_px))


@dataclass(frozen=True)
class AppConfig:
    audio: AudioConfig = AudioConfig()
    vad: VadConfig = VadConfig()
    whisper: WhisperConfig = WhisperConfig()
    animation: AnimationConfig = AnimationConfig()
    wake_words: tuple[str, ...] = ("彩花",)
    reply_text: str = "はい、社長。"
